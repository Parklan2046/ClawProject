using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NimingDalong;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace NimingDalong.Editor
{
    public static class WebBuild
    {
        private const string ScenePath = "Assets/Scenes/Login.unity";
        private const string TemplateName = "PROJECT:NimingDalong";

        private static readonly string[] RequiredAssets =
        {
            "Assets/Resources/Art/town-hybrid.jpg",
            "Assets/Resources/Audio/login-theme.mp3",
            "Assets/Resources/Fonts/NotoSansTC-Variable.ttf",
            "Assets/Resources/Fonts/NotoSerifTC-Variable.ttf",
            "Assets/WebGLTemplates/NimingDalong/index.html",
            "Assets/WebGLTemplates/NimingDalong/TemplateData/loading-desktop.png",
            "Assets/WebGLTemplates/NimingDalong/TemplateData/loading-mobile.png"
        };

        private static readonly string[] RuntimeShaders =
        {
            "Assets/Shaders/BackgroundUnlit.shader",
            "Assets/Shaders/Cloud.shader",
            "Assets/Shaders/ParticleAdditive.shader",
            "Assets/Shaders/ParticleAlpha.shader"
        };

        [MenuItem("逆命大郎/Build Web")]
        public static void Build()
        {
            ValidateAssets();
            ConfigureProject();
            CreateLoginScene();
            IncludeRuntimeShaders();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);

            string projectRoot = Directory.GetParent(Application.dataPath)?.FullName
                ?? throw new InvalidOperationException("Cannot resolve Unity project root.");
            string output = Environment.GetEnvironmentVariable("NIMING_UNITY_OUTPUT");
            if (string.IsNullOrWhiteSpace(output))
            {
                output = Path.Combine(projectRoot, "dist");
            }
            output = Path.GetFullPath(output);
            Directory.CreateDirectory(output);

            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = output,
                target = BuildTarget.WebGL,
                targetGroup = BuildTargetGroup.WebGL,
                options = BuildOptions.None
            };

            BuildReport report = BuildPipeline.BuildPlayer(options);
            BuildSummary summary = report.summary;
            Debug.Log(
                $"Unity Web build result={summary.result}, " +
                $"size={summary.totalSize:N0}, time={summary.totalTime}, output={output}");
            if (summary.result != BuildResult.Succeeded)
            {
                throw new BuildFailedException(
                    $"Unity Web build failed with result {summary.result} and {summary.totalErrors} errors.");
            }
        }

        [MenuItem("逆命大郎/Generate Login Scene")]
        public static void CreateLoginScene()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath) ?? "Assets/Scenes");
            Scene scene = EditorSceneManager.NewScene(
                NewSceneSetup.EmptyScene,
                NewSceneMode.Single);
            var app = new GameObject("NimingDalongLogin");
            app.AddComponent<LoginApp>();
            EditorSceneManager.MarkSceneDirty(scene);
            if (!EditorSceneManager.SaveScene(scene, ScenePath))
            {
                throw new InvalidOperationException($"Could not save generated scene: {ScenePath}");
            }
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(ScenePath, true)
            };
            Debug.Log($"Generated Unity login scene at {ScenePath}");
        }

        [MenuItem("逆命大郎/Validate Project")]
        public static void ValidateAssets()
        {
            string projectRoot = Directory.GetParent(Application.dataPath)?.FullName
                ?? throw new InvalidOperationException("Cannot resolve Unity project root.");
            var missing = RequiredAssets
                .Where(path => !File.Exists(Path.Combine(projectRoot, path)))
                .ToArray();
            if (missing.Length > 0)
            {
                throw new FileNotFoundException(
                    "Unity migration is missing required assets:\n" +
                    string.Join("\n", missing));
            }
            Debug.Log($"Validated {RequiredAssets.Length} required Unity migration assets.");
        }

        private static void ConfigureProject()
        {
            PlayerSettings.companyName = "逆命大郎製作組";
            PlayerSettings.productName = "逆命大郎";
            PlayerSettings.bundleVersion = "0.1.0-unity";
            PlayerSettings.colorSpace = ColorSpace.Gamma;
            PlayerSettings.runInBackground = true;
            PlayerSettings.defaultScreenWidth = 1440;
            PlayerSettings.defaultScreenHeight = 900;
            PlayerSettings.resizableWindow = true;

            PlayerSettings.WebGL.template = TemplateName;
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Gzip;
            PlayerSettings.WebGL.decompressionFallback = true;
            PlayerSettings.WebGL.dataCaching = true;

            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.WebGL, false);
            PlayerSettings.SetGraphicsAPIs(
                BuildTarget.WebGL,
                new[] { GraphicsDeviceType.OpenGLES3 });

            EditorUserBuildSettings.webGLBuildSubtarget =
                WebGLTextureSubtarget.Generic;
            EditorUserBuildSettings.SwitchActiveBuildTarget(
                BuildTargetGroup.WebGL,
                BuildTarget.WebGL);
        }

        private static void IncludeRuntimeShaders()
        {
            UnityEngine.Object[] settings =
                AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset");
            if (settings.Length == 0)
            {
                throw new InvalidOperationException("GraphicsSettings.asset is not available.");
            }

            var serialized = new SerializedObject(settings[0]);
            SerializedProperty shaders = serialized.FindProperty("m_AlwaysIncludedShaders");
            if (shaders == null || !shaders.isArray)
            {
                throw new InvalidOperationException(
                    "Unity GraphicsSettings does not expose the always-included shader list.");
            }

            var existing = new HashSet<Shader>();
            for (int i = 0; i < shaders.arraySize; i++)
            {
                var shader = shaders.GetArrayElementAtIndex(i).objectReferenceValue as Shader;
                if (shader != null)
                {
                    existing.Add(shader);
                }
            }

            foreach (string path in RuntimeShaders)
            {
                Shader shader = AssetDatabase.LoadAssetAtPath<Shader>(path);
                if (shader == null)
                {
                    throw new FileNotFoundException($"Required runtime shader is missing: {path}");
                }
                if (existing.Contains(shader))
                {
                    continue;
                }
                int index = shaders.arraySize;
                shaders.InsertArrayElementAtIndex(index);
                shaders.GetArrayElementAtIndex(index).objectReferenceValue = shader;
                existing.Add(shader);
            }
            serialized.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
