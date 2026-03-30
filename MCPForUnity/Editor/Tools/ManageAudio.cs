using System;
using System.Collections.Generic;
using MCPForUnity.Editor.Helpers;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Audio;

namespace MCPForUnity.Editor.Tools
{
    [McpForUnityTool("manage_audio", AutoRegister = false, Group = "core")]
    public static class ManageAudio
    {
        public static object HandleCommand(JObject @params)
        {
            if (@params == null)
                return new ErrorResponse("Parameters cannot be null.");

            var p = new ToolParams(@params);
            string action = p.Get("action")?.ToLowerInvariant();

            if (string.IsNullOrEmpty(action))
                return new ErrorResponse("'action' parameter is required.");

            try
            {
                switch (action)
                {
                    case "ping":
                        return new SuccessResponse("pong", new { tool = "manage_audio" });

                    case "get_audio_info":
                        return GetAudioInfo();

                    case "add_audio_source":
                        return AddAudioSource(@params, p);

                    case "configure_audio_source":
                        return ConfigureAudioSource(@params, p);

                    case "remove_audio_source":
                        return RemoveAudioSource(@params, p);

                    case "play":
                        return PlaySource(@params, p);

                    case "stop":
                        return StopSource(@params, p);

                    case "pause":
                        return PauseSource(@params, p);

                    case "unpause":
                        return UnpauseSource(@params, p);

                    case "play_clip_at_point":
                        return PlayClipAtPoint(@params, p);

                    case "set_clip":
                        return SetClip(@params, p);

                    case "get_clip_info":
                        return GetClipInfo(@params, p);

                    case "configure_import":
                        return ConfigureImport(@params, p);

                    case "ensure_listener":
                        return EnsureListener();

                    case "configure_listener":
                        return ConfigureListener(p);

                    case "add_reverb_zone":
                        return AddReverbZone(@params, p);

                    case "configure_reverb_zone":
                        return ConfigureReverbZone(@params, p);

                    case "find_mixers":
                        return FindMixers();

                    case "get_mixer_info":
                        return GetMixerInfo(p);

                    case "set_mixer_float":
                        return SetMixerFloat(p);

                    case "get_mixer_float":
                        return GetMixerFloat(p);

                    case "transition_to_snapshot":
                        return TransitionToSnapshot(p);

                    case "set_group_output":
                        return SetGroupOutput(@params, p);

                    default:
                        return new ErrorResponse($"Unknown action: '{action}'. Valid actions: " +
                            "ping, get_audio_info, add_audio_source, configure_audio_source, remove_audio_source, " +
                            "play, stop, pause, unpause, play_clip_at_point, " +
                            "set_clip, get_clip_info, configure_import, " +
                            "ensure_listener, configure_listener, " +
                            "add_reverb_zone, configure_reverb_zone, " +
                            "find_mixers, get_mixer_info, set_mixer_float, get_mixer_float, " +
                            "transition_to_snapshot, set_group_output.");
                }
            }
            catch (Exception ex)
            {
                McpLog.Error($"[ManageAudio] Action '{action}' failed: {ex}");
                return new ErrorResponse($"Error in action '{action}': {ex.Message}");
            }
        }

        // ---------------------------------------------------------------------------
        // Setup
        // ---------------------------------------------------------------------------

        private static object GetAudioInfo()
        {
#if UNITY_2023_1_OR_NEWER
            var sources = UnityEngine.Object.FindObjectsByType<AudioSource>(FindObjectsSortMode.None);
#else
            var sources = UnityEngine.Object.FindObjectsOfType<AudioSource>();
#endif
            var list = new List<object>();
            foreach (var src in sources)
            {
                list.Add(new
                {
                    gameObject = src.gameObject.name,
                    path = GetGameObjectPath(src.gameObject),
                    instanceId = src.gameObject.GetInstanceID(),
                    isPlaying = src.isPlaying,
                    volume = src.volume,
                    pitch = src.pitch,
                    loop = src.loop,
                    playOnAwake = src.playOnAwake,
                    spatialBlend = src.spatialBlend,
                    clip = src.clip != null ? AssetDatabase.GetAssetPath(src.clip) : null,
                    mute = src.mute,
                });
            }

            var listener = UnityEngine.Object.FindObjectOfType<AudioListener>();
            return new SuccessResponse($"Found {list.Count} AudioSource(s).", new
            {
                audioSources = list,
                listenerPresent = listener != null,
                listenerGameObject = listener != null ? listener.gameObject.name : null,
            });
        }

        // ---------------------------------------------------------------------------
        // AudioSource management
        // ---------------------------------------------------------------------------

        private static object AddAudioSource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            if (go.GetComponent<AudioSource>() != null)
                return new ErrorResponse($"GameObject '{go.name}' already has an AudioSource.");

            Undo.RecordObject(go, "Add AudioSource");
            var source = Undo.AddComponent<AudioSource>(go);

            ApplySourceProperties(source, p.GetRaw("properties") as JObject);
            EditorUtility.SetDirty(go);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"AudioSource added to '{go.name}'.", new
            {
                gameObject = go.name,
                instanceId = go.GetInstanceID(),
            });
        }

        private static object ConfigureAudioSource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            var props = p.GetRaw("properties") as JObject;
            if (props == null)
                return new ErrorResponse("'properties' parameter is required for configure_audio_source.");

            Undo.RecordObject(source, "Configure AudioSource");
            ApplySourceProperties(source, props);
            EditorUtility.SetDirty(source);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"AudioSource on '{go.name}' configured.", new
            {
                gameObject = go.name,
            });
        }

        private static object RemoveAudioSource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            Undo.DestroyObjectImmediate(source);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"AudioSource removed from '{go.name}'.");
        }

        // ---------------------------------------------------------------------------
        // Playback
        // ---------------------------------------------------------------------------

        private static object PlaySource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            if (!EditorApplication.isPlaying)
                return new SuccessResponse($"AudioSource on '{go.name}' is ready. Play is only effective in Play Mode.", new { editMode = true });

            source.Play();
            return new SuccessResponse($"AudioSource on '{go.name}' is playing.");
        }

        private static object StopSource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            if (!EditorApplication.isPlaying)
                return new SuccessResponse($"AudioSource on '{go.name}' noted. Stop is only effective in Play Mode.", new { editMode = true });

            source.Stop();
            return new SuccessResponse($"AudioSource on '{go.name}' stopped.");
        }

        private static object PauseSource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            if (!EditorApplication.isPlaying)
                return new SuccessResponse($"AudioSource on '{go.name}' noted. Pause is only effective in Play Mode.", new { editMode = true });

            source.Pause();
            return new SuccessResponse($"AudioSource on '{go.name}' paused.");
        }

        private static object UnpauseSource(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            if (!EditorApplication.isPlaying)
                return new SuccessResponse($"AudioSource on '{go.name}' noted. Unpause is only effective in Play Mode.", new { editMode = true });

            source.UnPause();
            return new SuccessResponse($"AudioSource on '{go.name}' unpaused.");
        }

        private static object PlayClipAtPoint(JObject @params, ToolParams p)
        {
            var props = p.GetRaw("properties") as JObject ?? new JObject();
            var pp = new ToolParams(props);

            string clipPath = p.Get("clipPath") ?? pp.Get("clipPath") ?? pp.Get("clip_path");
            if (string.IsNullOrEmpty(clipPath))
                return new ErrorResponse("'clipPath' is required for play_clip_at_point (in properties or top-level).");

            var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(clipPath);
            if (clip == null)
                return new ErrorResponse($"AudioClip not found at '{clipPath}'.");

            float vol = pp.GetFloat("volume") ?? 1f;
            var posToken = props["position"] ?? @params["position"];
            Vector3 pos = ParseVector3(posToken) ?? Vector3.zero;

            if (!EditorApplication.isPlaying)
                return new SuccessResponse($"Clip '{clip.name}' ready. PlayClipAtPoint is only effective in Play Mode.", new { editMode = true, clipPath, position = pos.ToString() });

            AudioSource.PlayClipAtPoint(clip, pos, vol);
            return new SuccessResponse($"Playing clip '{clip.name}' at {pos}.");
        }

        // ---------------------------------------------------------------------------
        // Clip management
        // ---------------------------------------------------------------------------

        private static object SetClip(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            string clipPath = p.Get("clipPath");
            if (string.IsNullOrEmpty(clipPath))
                return new ErrorResponse("'clipPath' parameter is required for set_clip.");

            var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(clipPath);
            if (clip == null)
                return new ErrorResponse($"AudioClip not found at '{clipPath}'.");

            Undo.RecordObject(source, "Set AudioSource Clip");
            source.clip = clip;
            EditorUtility.SetDirty(source);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"Clip '{clip.name}' assigned to AudioSource on '{go.name}'.", new
            {
                clipName = clip.name,
                clipPath,
            });
        }

        private static object GetClipInfo(JObject @params, ToolParams p)
        {
            string clipPath = p.Get("clipPath");
            if (string.IsNullOrEmpty(clipPath))
            {
                // Fall back to reading clip from AudioSource on target
                var go = FindTarget(@params, p);
                if (go == null)
                    return new ErrorResponse("Provide 'clipPath' or a 'target' with an AudioSource.");

                var src = go.GetComponent<AudioSource>();
                if (src == null || src.clip == null)
                    return new ErrorResponse($"No AudioClip found on '{go?.name ?? "target"}'.");

                return ClipInfoResponse(src.clip);
            }

            var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(clipPath);
            if (clip == null)
                return new ErrorResponse($"AudioClip not found at '{clipPath}'.");

            return ClipInfoResponse(clip);
        }

        private static object ClipInfoResponse(AudioClip clip)
        {
            return new SuccessResponse($"Clip info for '{clip.name}'.", new
            {
                name = clip.name,
                path = AssetDatabase.GetAssetPath(clip),
                length = clip.length,
                samples = clip.samples,
                channels = clip.channels,
                frequency = clip.frequency,
                loadType = clip.loadType.ToString(),
                ambisonic = clip.ambisonic,
            });
        }

        private static object ConfigureImport(JObject @params, ToolParams p)
        {
            string clipPath = p.Get("clipPath");
            if (string.IsNullOrEmpty(clipPath))
                return new ErrorResponse("'clipPath' parameter is required for configure_import.");

            var importer = AssetImporter.GetAtPath(clipPath) as AudioImporter;
            if (importer == null)
                return new ErrorResponse($"No AudioImporter found at '{clipPath}'. Ensure the path points to an audio asset.");

            var props = p.GetRaw("properties") as JObject ?? new JObject();
            var pp = new ToolParams(props);

            bool changed = false;

            bool forceToMono = pp.GetBool("forceToMono", importer.forceToMono);
            if (forceToMono != importer.forceToMono) { importer.forceToMono = forceToMono; changed = true; }

            bool loadInBackground = pp.GetBool("loadInBackground", importer.loadInBackground);
            if (loadInBackground != importer.loadInBackground) { importer.loadInBackground = loadInBackground; changed = true; }

            bool preloadAudioData = pp.GetBool("preloadAudioData", importer.preloadAudioData);
            if (preloadAudioData != importer.preloadAudioData) { importer.preloadAudioData = preloadAudioData; changed = true; }

            var defaultSettings = importer.defaultSampleSettings;
            bool settingsChanged = false;

            string compressionFormat = pp.Get("compressionFormat");
            if (!string.IsNullOrEmpty(compressionFormat) && Enum.TryParse<AudioCompressionFormat>(compressionFormat, true, out var fmt))
            {
                defaultSettings.compressionFormat = fmt;
                settingsChanged = true;
            }

            float? quality = pp.GetFloat("quality");
            if (quality.HasValue)
            {
                defaultSettings.quality = Mathf.Clamp01(quality.Value);
                settingsChanged = true;
            }

            string sampleRateSetting = pp.Get("sampleRateSetting");
            if (!string.IsNullOrEmpty(sampleRateSetting) && Enum.TryParse<AudioSampleRateSetting>(sampleRateSetting, true, out var srs))
            {
                defaultSettings.sampleRateSetting = srs;
                settingsChanged = true;
            }

            if (settingsChanged)
            {
                importer.defaultSampleSettings = defaultSettings;
                changed = true;
            }

            if (changed)
            {
                EditorUtility.SetDirty(importer);
                importer.SaveAndReimport();
            }

            return new SuccessResponse($"AudioImporter settings updated for '{clipPath}'.", new { changed });
        }

        // ---------------------------------------------------------------------------
        // AudioListener
        // ---------------------------------------------------------------------------

        private static object EnsureListener()
        {
            var listener = UnityEngine.Object.FindObjectOfType<AudioListener>();
            if (listener != null)
            {
                return new SuccessResponse($"AudioListener already exists on '{listener.gameObject.name}'.", new
                {
                    gameObject = listener.gameObject.name,
                    instanceId = listener.gameObject.GetInstanceID(),
                    created = false,
                });
            }

            // Create a new GameObject with an AudioListener
            var go = new GameObject("AudioListener");
            Undo.RegisterCreatedObjectUndo(go, "Create AudioListener");
            Undo.AddComponent<AudioListener>(go);

            return new SuccessResponse("AudioListener created on new GameObject 'AudioListener'.", new
            {
                gameObject = go.name,
                instanceId = go.GetInstanceID(),
                created = true,
            });
        }

        private static object ConfigureListener(ToolParams p)
        {
            var props = p.GetRaw("properties") as JObject ?? new JObject();
            var pp = new ToolParams(props);

            float? volume = pp.GetFloat("volume");
            if (volume.HasValue)
                AudioListener.volume = Mathf.Clamp01(volume.Value);

            bool? pause = pp.GetBool("pause") ? true : (bool?)null;
            string pauseStr = pp.Get("pause");
            if (!string.IsNullOrEmpty(pauseStr))
            {
                if (bool.TryParse(pauseStr, out var pauseVal))
                    AudioListener.pause = pauseVal;
            }

            return new SuccessResponse("AudioListener configured.", new
            {
                volume = AudioListener.volume,
                pause = AudioListener.pause,
            });
        }

        // ---------------------------------------------------------------------------
        // AudioReverbZone
        // ---------------------------------------------------------------------------

        private static object AddReverbZone(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            Undo.RecordObject(go, "Add AudioReverbZone");
            var zone = Undo.AddComponent<AudioReverbZone>(go);

            var props = p.GetRaw("properties") as JObject;
            if (props != null)
                ApplyReverbZoneProperties(zone, new ToolParams(props));

            EditorUtility.SetDirty(go);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"AudioReverbZone added to '{go.name}'.", new
            {
                gameObject = go.name,
                reverbPreset = zone.reverbPreset.ToString(),
            });
        }

        private static object ConfigureReverbZone(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var zone = go.GetComponent<AudioReverbZone>();
            if (zone == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioReverbZone.");

            var props = p.GetRaw("properties") as JObject;
            if (props == null)
                return new ErrorResponse("'properties' parameter is required for configure_reverb_zone.");

            Undo.RecordObject(zone, "Configure AudioReverbZone");
            ApplyReverbZoneProperties(zone, new ToolParams(props));
            EditorUtility.SetDirty(zone);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"AudioReverbZone on '{go.name}' configured.", new
            {
                gameObject = go.name,
                reverbPreset = zone.reverbPreset.ToString(),
            });
        }

        // ---------------------------------------------------------------------------
        // AudioMixer
        // ---------------------------------------------------------------------------

        private static object FindMixers()
        {
            var guids = AssetDatabase.FindAssets("t:AudioMixer");
            var results = new List<object>();
            foreach (var guid in guids)
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var mixer = AssetDatabase.LoadAssetAtPath<AudioMixer>(path);
                if (mixer == null) continue;
                results.Add(new { name = mixer.name, path });
            }
            return new SuccessResponse($"Found {results.Count} AudioMixer asset(s).", new { mixers = results });
        }

        private static object GetMixerInfo(ToolParams p)
        {
            var mixer = LoadMixer(p, out string err);
            if (mixer == null) return new ErrorResponse(err);

            // Groups
            var allGroups = mixer.FindMatchingGroups(string.Empty);
            var groups = new List<object>();
            foreach (var g in allGroups)
                groups.Add(new { name = g.name, path = GetGroupPath(g) });

            // Snapshots and exposed params via SerializedObject
            var snapshots = new List<string>();
            var exposedParams = new List<string>();
            var so = new UnityEditor.SerializedObject(mixer);

            var snapshotsProp = so.FindProperty("m_Snapshots");
            if (snapshotsProp != null)
            {
                for (int i = 0; i < snapshotsProp.arraySize; i++)
                {
                    var snapRef = snapshotsProp.GetArrayElementAtIndex(i).objectReferenceValue;
                    if (snapRef != null) snapshots.Add(snapRef.name);
                }
            }

            var exposedProp = so.FindProperty("m_ExposedParameters");
            if (exposedProp != null)
            {
                for (int i = 0; i < exposedProp.arraySize; i++)
                {
                    var elem = exposedProp.GetArrayElementAtIndex(i);
                    var nameProp = elem.FindPropertyRelative("name");
                    if (nameProp != null) exposedParams.Add(nameProp.stringValue);
                }
            }

            return new SuccessResponse($"Mixer info for '{mixer.name}'.", new
            {
                name = mixer.name,
                path = AssetDatabase.GetAssetPath(mixer),
                groups,
                snapshots,
                exposedParameters = exposedParams,
            });
        }

        private static object SetMixerFloat(ToolParams p)
        {
            var mixer = LoadMixer(p, out string err);
            if (mixer == null) return new ErrorResponse(err);

            var props = p.GetRaw("properties") as JObject ?? new JObject();
            var pp = new ToolParams(props);

            string paramName = pp.Get("paramName");
            if (string.IsNullOrEmpty(paramName))
                return new ErrorResponse("'properties.paramName' is required for set_mixer_float.");

            float? value = pp.GetFloat("value");
            if (!value.HasValue)
                return new ErrorResponse("'properties.value' is required for set_mixer_float.");

            if (!mixer.SetFloat(paramName, value.Value))
                return new ErrorResponse($"Parameter '{paramName}' not found on mixer '{mixer.name}'. Ensure it is exposed in the AudioMixer.");

            return new SuccessResponse($"Set '{paramName}' = {value.Value} on mixer '{mixer.name}'.", new
            {
                paramName,
                value = value.Value,
            });
        }

        private static object GetMixerFloat(ToolParams p)
        {
            var mixer = LoadMixer(p, out string err);
            if (mixer == null) return new ErrorResponse(err);

            var props = p.GetRaw("properties") as JObject ?? new JObject();
            string paramName = new ToolParams(props).Get("paramName");
            if (string.IsNullOrEmpty(paramName))
                return new ErrorResponse("'properties.paramName' is required for get_mixer_float.");

            if (!mixer.GetFloat(paramName, out float value))
                return new ErrorResponse($"Parameter '{paramName}' not found on mixer '{mixer.name}'. Ensure it is exposed in the AudioMixer.");

            return new SuccessResponse($"Got '{paramName}' = {value} from mixer '{mixer.name}'.", new
            {
                paramName,
                value,
            });
        }

        private static object TransitionToSnapshot(ToolParams p)
        {
            var mixer = LoadMixer(p, out string err);
            if (mixer == null) return new ErrorResponse(err);

            var props = p.GetRaw("properties") as JObject ?? new JObject();
            var pp = new ToolParams(props);

            string snapshotName = pp.Get("snapshotName");
            if (string.IsNullOrEmpty(snapshotName))
                return new ErrorResponse("'properties.snapshotName' is required for transition_to_snapshot.");

            float timeToReach = pp.GetFloat("timeToReach") ?? 0f;

            var snapshot = mixer.FindSnapshot(snapshotName);
            if (snapshot == null)
                return new ErrorResponse($"Snapshot '{snapshotName}' not found on mixer '{mixer.name}'.");

            if (!EditorApplication.isPlaying)
                return new SuccessResponse($"Snapshot '{snapshotName}' found. TransitionTo is only effective in Play Mode.", new { editMode = true, snapshotName, timeToReach });

            snapshot.TransitionTo(timeToReach);
            return new SuccessResponse($"Transitioning to snapshot '{snapshotName}' over {timeToReach}s.");
        }

        private static object SetGroupOutput(JObject @params, ToolParams p)
        {
            var go = FindTarget(@params, p);
            if (go == null) return new ErrorResponse(TargetNotFoundMessage(p));

            var source = go.GetComponent<AudioSource>();
            if (source == null)
                return new ErrorResponse($"GameObject '{go.name}' does not have an AudioSource.");

            var mixer = LoadMixer(p, out string err);
            if (mixer == null) return new ErrorResponse(err);

            var props = p.GetRaw("properties") as JObject ?? new JObject();
            string groupPath = new ToolParams(props).Get("group") ?? "Master";

            var matches = mixer.FindMatchingGroups(groupPath);
            if (matches == null || matches.Length == 0)
                return new ErrorResponse($"Group '{groupPath}' not found in mixer '{mixer.name}'.");

            Undo.RecordObject(source, "Set AudioSource Mixer Group");
            source.outputAudioMixerGroup = matches[0];
            EditorUtility.SetDirty(source);
            SceneHelper.MarkOwningSceneDirty(go);

            return new SuccessResponse($"AudioSource on '{go.name}' routed to mixer group '{matches[0].name}'.", new
            {
                gameObject = go.name,
                mixerGroup = matches[0].name,
            });
        }

        private static AudioMixer LoadMixer(ToolParams p, out string error)
        {
            string mixerPath = p.Get("mixerPath");
            if (string.IsNullOrEmpty(mixerPath))
            {
                error = "'mixerPath' parameter is required (e.g. 'Assets/Audio/MainMixer.mixer').";
                return null;
            }
            var mixer = AssetDatabase.LoadAssetAtPath<AudioMixer>(mixerPath);
            if (mixer == null)
            {
                error = $"AudioMixer not found at '{mixerPath}'.";
                return null;
            }
            error = null;
            return mixer;
        }

        private static string GetGroupPath(AudioMixerGroup group)
        {
            // AudioMixerGroup has no parent API in public Unity, so we return the name
            return group.name;
        }

        // ---------------------------------------------------------------------------
        // Helpers
        // ---------------------------------------------------------------------------

        private static void ApplySourceProperties(AudioSource source, JObject props)
        {
            if (props == null) return;
            var p = new ToolParams(props);

            float? volume = p.GetFloat("volume");
            if (volume.HasValue) source.volume = Mathf.Clamp01(volume.Value);

            float? pitch = p.GetFloat("pitch");
            if (pitch.HasValue) source.pitch = pitch.Value;

            if (p.Has("loop")) source.loop = p.GetBool("loop");
            if (p.Has("playOnAwake")) source.playOnAwake = p.GetBool("playOnAwake");
            if (p.Has("mute")) source.mute = p.GetBool("mute");
            if (p.Has("bypassEffects")) source.bypassEffects = p.GetBool("bypassEffects");
            if (p.Has("bypassListenerEffects")) source.bypassListenerEffects = p.GetBool("bypassListenerEffects");
            if (p.Has("bypassReverbZones")) source.bypassReverbZones = p.GetBool("bypassReverbZones");

            float? spatialBlend = p.GetFloat("spatialBlend");
            if (spatialBlend.HasValue) source.spatialBlend = Mathf.Clamp01(spatialBlend.Value);

            float? minDistance = p.GetFloat("minDistance");
            if (minDistance.HasValue) source.minDistance = minDistance.Value;

            float? maxDistance = p.GetFloat("maxDistance");
            if (maxDistance.HasValue) source.maxDistance = maxDistance.Value;

            string rolloffMode = p.Get("rolloffMode");
            if (!string.IsNullOrEmpty(rolloffMode) && Enum.TryParse<AudioRolloffMode>(rolloffMode, true, out var mode))
                source.rolloffMode = mode;

            int? priority = p.GetInt("priority");
            if (priority.HasValue) source.priority = Mathf.Clamp(priority.Value, 0, 256);

            float? panStereo = p.GetFloat("panStereo");
            if (panStereo.HasValue) source.panStereo = Mathf.Clamp(panStereo.Value, -1f, 1f);

            float? dopplerLevel = p.GetFloat("dopplerLevel");
            if (dopplerLevel.HasValue) source.dopplerLevel = dopplerLevel.Value;

            float? spread = p.GetFloat("spread");
            if (spread.HasValue) source.spread = Mathf.Clamp(spread.Value, 0f, 360f);

            string mixerGroupPath = p.Get("outputAudioMixerGroup");
            if (!string.IsNullOrEmpty(mixerGroupPath))
            {
                var mixer = AssetDatabase.LoadAssetAtPath<AudioMixer>(mixerGroupPath);
                if (mixer != null)
                {
                    var groups = mixer.FindMatchingGroups("Master");
                    if (groups != null && groups.Length > 0)
                        source.outputAudioMixerGroup = groups[0];
                }
            }
        }

        private static void ApplyReverbZoneProperties(AudioReverbZone zone, ToolParams p)
        {
            string preset = p.Get("reverbPreset");
            if (!string.IsNullOrEmpty(preset) && Enum.TryParse<AudioReverbPreset>(preset, true, out var reverbPreset))
                zone.reverbPreset = reverbPreset;

            float? minDistance = p.GetFloat("minDistance");
            if (minDistance.HasValue) zone.minDistance = minDistance.Value;

            float? maxDistance = p.GetFloat("maxDistance");
            if (maxDistance.HasValue) zone.maxDistance = maxDistance.Value;

            int? room = p.GetInt("room");
            if (room.HasValue) zone.room = room.Value;

            int? roomHF = p.GetInt("roomHF");
            if (roomHF.HasValue) zone.roomHF = roomHF.Value;

            int? roomLF = p.GetInt("roomLF");
            if (roomLF.HasValue) zone.roomLF = roomLF.Value;

            float? decayTime = p.GetFloat("decayTime");
            if (decayTime.HasValue) zone.decayTime = decayTime.Value;

            float? decayHFRatio = p.GetFloat("decayHFRatio");
            if (decayHFRatio.HasValue) zone.decayHFRatio = decayHFRatio.Value;

            int? reflections = p.GetInt("reflections");
            if (reflections.HasValue) zone.reflections = reflections.Value;

            float? reflectionsDelay = p.GetFloat("reflectionsDelay");
            if (reflectionsDelay.HasValue) zone.reflectionsDelay = reflectionsDelay.Value;

            int? reverb = p.GetInt("reverb");
            if (reverb.HasValue) zone.reverb = reverb.Value;

            float? reverbDelay = p.GetFloat("reverbDelay");
            if (reverbDelay.HasValue) zone.reverbDelay = reverbDelay.Value;

            float? hfReference = p.GetFloat("hfReference");
            if (hfReference.HasValue) zone.HFReference = hfReference.Value;

            float? lfReference = p.GetFloat("lfReference");
            if (lfReference.HasValue) zone.LFReference = lfReference.Value;

            float? diffusion = p.GetFloat("diffusion");
            if (diffusion.HasValue) zone.diffusion = diffusion.Value;

            float? density = p.GetFloat("density");
            if (density.HasValue) zone.density = density.Value;
        }

        private static GameObject FindTarget(JObject @params, ToolParams p)
        {
            var targetToken = @params["target"];
            if (targetToken == null) return null;
            string searchMethod = p.Get("searchMethod") ?? p.Get("search_method");
            return GameObjectLookup.FindByTarget(targetToken, searchMethod, includeInactive: true);
        }

        private static string TargetNotFoundMessage(ToolParams p)
        {
            string target = p.Get("target");
            string method = p.Get("searchMethod") ?? p.Get("search_method") ?? "by_name";
            return $"Target GameObject '{target}' not found using method '{method}'.";
        }

        private static string GetGameObjectPath(GameObject go)
        {
            string path = go.name;
            var parent = go.transform.parent;
            while (parent != null)
            {
                path = parent.name + "/" + path;
                parent = parent.parent;
            }
            return path;
        }

        private static Vector3? ParseVector3(JToken token)
        {
            if (token == null) return null;
            if (token.Type == JTokenType.Array)
            {
                var arr = token as JArray;
                if (arr != null && arr.Count >= 3)
                {
                    if (float.TryParse(arr[0].ToString(), out float x) &&
                        float.TryParse(arr[1].ToString(), out float y) &&
                        float.TryParse(arr[2].ToString(), out float z))
                        return new Vector3(x, y, z);
                }
            }
            return null;
        }
    }
}
