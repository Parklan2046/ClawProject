using System.Collections.Generic;
using UnityEngine;

namespace NimingDalong
{
    internal sealed class LoginEnvironment : MonoBehaviour
    {
        private readonly struct ViewportAnchor
        {
            public readonly Transform transform;
            public readonly Vector2 desktop;
            public readonly Vector2 mobile;
            public readonly float depth;
            public readonly bool hideOnMobile;

            public ViewportAnchor(
                Transform transform,
                Vector2 desktop,
                Vector2 mobile,
                float depth,
                bool hideOnMobile = false)
            {
                this.transform = transform;
                this.desktop = desktop;
                this.mobile = mobile;
                this.depth = depth;
                this.hideOnMobile = hideOnMobile;
            }
        }

        private Camera _camera;
        private Renderer _background;
        private Texture2D _backdrop;
        private bool _reducedMotion;
        private int _lastWidth;
        private int _lastHeight;
        private readonly List<ViewportAnchor> _anchors = new();

        public static LoginEnvironment Build(
            Camera camera,
            Texture2D backdrop,
            bool reducedMotion)
        {
            var root = new GameObject("HybridTownEnvironment");
            var environment = root.AddComponent<LoginEnvironment>();
            environment._camera = camera;
            environment._backdrop = backdrop;
            environment._reducedMotion = reducedMotion;
            environment.Construct();
            return environment;
        }

        private void Construct()
        {
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = UiFactory.Html("#425D77") * 0.72f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = UiFactory.Html("#172B3C");
            RenderSettings.fogDensity = 0.0085f;

            var moon = new GameObject("Moonlight").AddComponent<Light>();
            moon.transform.SetParent(transform, false);
            moon.type = LightType.Directional;
            moon.color = UiFactory.Html("#ADCBE8");
            moon.intensity = 0.62f;
            moon.transform.rotation = Quaternion.Euler(48f, -26f, 0f);
            moon.shadows = LightShadows.None;

            var warmFill = new GameObject("WarmFill").AddComponent<Light>();
            warmFill.transform.SetParent(transform, false);
            warmFill.type = LightType.Directional;
            warmFill.color = UiFactory.Html("#D17B55");
            warmFill.intensity = 0.22f;
            warmFill.transform.rotation = Quaternion.Euler(36f, 155f, 0f);
            warmFill.shadows = LightShadows.None;

            BuildBackground();
            BuildClouds();
            BuildLanterns();

            Transform leftFire = BuildBrazier("LeftFire", 1f);
            _anchors.Add(new ViewportAnchor(
                leftFire,
                new Vector2(0.325f, 0.235f),
                new Vector2(0.10f, 0.26f),
                9.5f));

            Transform distantFire = BuildBrazier("DistantFire", 0.56f);
            _anchors.Add(new ViewportAnchor(
                distantFire,
                new Vector2(0.602f, 0.455f),
                new Vector2(0.88f, 0.47f),
                13.8f,
                true));

            ApplyLayout(true);
        }

        private void BuildBackground()
        {
            var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad.name = "PaintedTownBackdrop";
            quad.transform.SetParent(transform, false);
            Destroy(quad.GetComponent<Collider>());

            var shader = Shader.Find("Niming/BackgroundUnlit");
            if (shader == null)
            {
                shader = Shader.Find("Unlit/Texture");
            }
            var material = new Material(shader)
            {
                name = "PaintedTownMaterial",
                mainTexture = _backdrop
            };
            if (material.HasProperty("_Tint"))
            {
                material.SetColor("_Tint", Color.white);
            }
            _background = quad.GetComponent<Renderer>();
            _background.sharedMaterial = material;
        }

        private void BuildClouds()
        {
            var shader = Shader.Find("Niming/Cloud");
            if (shader == null)
            {
                return;
            }

            var specs = new[]
            {
                new Vector4(0.18f, 0.78f, 20.0f, 0.20f),
                new Vector4(0.52f, 0.86f, 21.0f, 0.14f),
                new Vector4(0.78f, 0.72f, 19.0f, 0.16f)
            };

            for (int i = 0; i < specs.Length; i++)
            {
                var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
                quad.name = $"MovingCloud_{i + 1}";
                quad.transform.SetParent(transform, false);
                Destroy(quad.GetComponent<Collider>());
                var material = new Material(shader)
                {
                    name = $"CloudMaterial_{i + 1}"
                };
                material.SetFloat("_Seed", 2.7f + i * 8.3f);
                material.SetFloat("_Opacity", specs[i].w);
                material.SetFloat("_Speed", _reducedMotion ? 0f : 0.018f + i * 0.006f);
                quad.GetComponent<Renderer>().sharedMaterial = material;
                quad.transform.localScale = new Vector3(8.4f + i * 2.1f, 2.4f, 1f);
                _anchors.Add(new ViewportAnchor(
                    quad.transform,
                    new Vector2(specs[i].x, specs[i].y),
                    new Vector2(specs[i].x, specs[i].y),
                    specs[i].z,
                    i == 2));
            }
        }

        private void BuildLanterns()
        {
            var lanternPositions = new[]
            {
                new Vector2(0.278f, 0.34f),
                new Vector2(0.354f, 0.42f),
                new Vector2(0.410f, 0.47f),
                new Vector2(0.452f, 0.505f)
            };

            for (int i = 0; i < lanternPositions.Length; i++)
            {
                Transform lantern = CreateLantern($"Lantern_{i + 1}", 0.72f - i * 0.08f, i);
                _anchors.Add(new ViewportAnchor(
                    lantern,
                    lanternPositions[i],
                    new Vector2(-0.08f + i * 0.11f, 0.40f + i * 0.035f),
                    11.2f + i * 1.1f,
                    i > 1));
            }
        }

        private Transform CreateLantern(string name, float scale, int index)
        {
            var root = new GameObject(name).transform;
            root.SetParent(transform, false);
            root.localScale = Vector3.one * scale;

            var postMaterial = CreateStandardMaterial(
                UiFactory.Html("#171719"),
                0.88f,
                0.18f);
            var lanternMaterial = CreateStandardMaterial(
                UiFactory.Html("#8E1F1B"),
                0.48f,
                0f,
                UiFactory.Html("#F0442F"),
                1.25f);

            Transform post = Primitive(
                PrimitiveType.Cylinder,
                "Post",
                root,
                new Vector3(0f, -0.55f, 0f),
                new Vector3(0.055f, 0.72f, 0.055f),
                postMaterial);
            post.localRotation = Quaternion.identity;

            Transform arm = Primitive(
                PrimitiveType.Cube,
                "CrossArm",
                root,
                new Vector3(-0.16f, 0.12f, 0f),
                new Vector3(0.38f, 0.045f, 0.045f),
                postMaterial);
            arm.localRotation = Quaternion.identity;

            Transform body = Primitive(
                PrimitiveType.Sphere,
                "LanternBody",
                root,
                new Vector3(-0.32f, -0.05f, 0f),
                new Vector3(0.23f, 0.34f, 0.23f),
                lanternMaterial);
            var motion = body.gameObject.AddComponent<WuxiaAmbientMotion>();
            motion.phase = index * 1.7f;
            motion.enabled = !_reducedMotion;

            Primitive(
                PrimitiveType.Cylinder,
                "LanternCapTop",
                body,
                new Vector3(0f, 0.54f, 0f),
                new Vector3(0.72f, 0.08f, 0.72f),
                postMaterial);
            Primitive(
                PrimitiveType.Cylinder,
                "LanternCapBottom",
                body,
                new Vector3(0f, -0.54f, 0f),
                new Vector3(0.72f, 0.08f, 0.72f),
                postMaterial);
            Primitive(
                PrimitiveType.Cylinder,
                "Tassel",
                body,
                new Vector3(0f, -0.78f, 0f),
                new Vector3(0.08f, 0.28f, 0.08f),
                lanternMaterial);

            var light = new GameObject("LanternGlow").AddComponent<Light>();
            light.transform.SetParent(body, false);
            light.transform.localPosition = Vector3.zero;
            light.type = LightType.Point;
            light.color = UiFactory.Html("#F04A31");
            light.intensity = 0.62f;
            light.range = 2.6f;
            light.shadows = LightShadows.None;

            return root;
        }

        private Transform BuildBrazier(string name, float scale)
        {
            var root = new GameObject(name).transform;
            root.SetParent(transform, false);
            root.localScale = Vector3.one * scale;

            var darkMetal = CreateStandardMaterial(
                UiFactory.Html("#1C1919"),
                0.72f,
                0.72f);
            var brass = CreateStandardMaterial(
                UiFactory.Html("#76502E"),
                0.42f,
                0.68f);
            var emberMaterial = CreateStandardMaterial(
                UiFactory.Html("#24100B"),
                0.94f,
                0f,
                UiFactory.Html("#B53B18"),
                0.76f);

            Primitive(
                PrimitiveType.Cylinder,
                "Pedestal",
                root,
                new Vector3(0f, -0.42f, 0f),
                new Vector3(0.34f, 0.48f, 0.34f),
                brass);
            Primitive(
                PrimitiveType.Cylinder,
                "Bowl",
                root,
                new Vector3(0f, 0.02f, 0f),
                new Vector3(0.58f, 0.13f, 0.58f),
                darkMetal);

            for (int i = 0; i < 3; i++)
            {
                Transform coal = Primitive(
                    PrimitiveType.Cylinder,
                    $"Charcoal_{i + 1}",
                    root,
                    new Vector3(0f, 0.18f + i * 0.025f, 0f),
                    new Vector3(0.075f, 0.42f, 0.075f),
                    emberMaterial);
                coal.localRotation = Quaternion.Euler(0f, i * 57f - 30f, 90f);
            }

            BuildFlameParticles(root);
            BuildEmberParticles(root);
            BuildSmokeParticles(root);

            var light = new GameObject("FireLight").AddComponent<Light>();
            light.transform.SetParent(root, false);
            light.transform.localPosition = new Vector3(0f, 0.72f, 0f);
            light.type = LightType.Point;
            light.color = UiFactory.Html("#FF8E45");
            light.intensity = 1.55f;
            light.range = 4.6f;
            light.shadows = LightShadows.None;
            var flicker = light.gameObject.AddComponent<FireLightFlicker>();
            flicker.enabled = !_reducedMotion;
            return root;
        }

        private void BuildFlameParticles(Transform parent)
        {
            var ps = CreateParticleSystem("FlameWisps", parent);
            var main = ps.main;
            main.loop = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.58f, 0.94f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.38f, 0.92f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.30f, 0.62f);
            main.startRotation = new ParticleSystem.MinMaxCurve(-0.24f, 0.24f);
            main.simulationSpace = ParticleSystemSimulationSpace.Local;
            main.simulationSpeed = _reducedMotion ? 0f : 1f;
            main.maxParticles = 72;

            var emission = ps.emission;
            emission.rateOverTime = _reducedMotion ? 0f : 38f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 9f;
            shape.radius = 0.27f;
            shape.position = new Vector3(0f, 0.20f, 0f);

            var colors = ps.colorOverLifetime;
            colors.enabled = true;
            colors.color = new ParticleSystem.MinMaxGradient(Gradient(
                new[]
                {
                    new GradientColorKey(UiFactory.Html("#FFF0AE"), 0f),
                    new GradientColorKey(UiFactory.Html("#FF9B32"), 0.34f),
                    new GradientColorKey(UiFactory.Html("#E43D13"), 0.75f),
                    new GradientColorKey(UiFactory.Html("#681109"), 1f)
                },
                new[]
                {
                    new GradientAlphaKey(0.96f, 0f),
                    new GradientAlphaKey(0.88f, 0.46f),
                    new GradientAlphaKey(0f, 1f)
                }));

            var size = ps.sizeOverLifetime;
            size.enabled = true;
            size.size = new ParticleSystem.MinMaxCurve(
                1f,
                new AnimationCurve(
                    new Keyframe(0f, 0.34f),
                    new Keyframe(0.24f, 1f),
                    new Keyframe(0.72f, 0.58f),
                    new Keyframe(1f, 0f)));

            var noise = ps.noise;
            noise.enabled = !_reducedMotion;
            noise.strength = 0.15f;
            noise.frequency = 0.72f;
            noise.scrollSpeed = 0.42f;
            noise.quality = ParticleSystemNoiseQuality.Low;

            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Billboard;
            renderer.sharedMaterial = ParticleMaterial(
                "Niming/ParticleAdditive",
                CreateFlameTexture());
            renderer.sortingFudge = 1.2f;
            if (_reducedMotion)
            {
                ps.Emit(12);
            }
        }

        private void BuildEmberParticles(Transform parent)
        {
            var ps = CreateParticleSystem("Embers", parent);
            var main = ps.main;
            main.loop = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.9f, 1.8f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.8f, 1.8f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.022f, 0.055f);
            main.simulationSpace = ParticleSystemSimulationSpace.Local;
            main.maxParticles = 36;

            var emission = ps.emission;
            emission.rateOverTime = _reducedMotion ? 0f : 8f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Hemisphere;
            shape.radius = 0.22f;
            shape.position = new Vector3(0f, 0.26f, 0f);

            var colors = ps.colorOverLifetime;
            colors.enabled = true;
            colors.color = new ParticleSystem.MinMaxGradient(Gradient(
                new[]
                {
                    new GradientColorKey(UiFactory.Html("#FFE29A"), 0f),
                    new GradientColorKey(UiFactory.Html("#FF6B21"), 0.55f),
                    new GradientColorKey(UiFactory.Html("#7A1309"), 1f)
                },
                new[]
                {
                    new GradientAlphaKey(1f, 0f),
                    new GradientAlphaKey(0.72f, 0.7f),
                    new GradientAlphaKey(0f, 1f)
                }));

            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Stretch;
            renderer.velocityScale = 0.18f;
            renderer.lengthScale = 1.8f;
            renderer.sharedMaterial = ParticleMaterial(
                "Niming/ParticleAdditive",
                CreateSoftCircleTexture());
        }

        private void BuildSmokeParticles(Transform parent)
        {
            var ps = CreateParticleSystem("Smoke", parent);
            var main = ps.main;
            main.loop = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(1.7f, 2.8f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.18f, 0.42f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.32f, 0.72f);
            main.startRotation = new ParticleSystem.MinMaxCurve(-Mathf.PI, Mathf.PI);
            main.simulationSpace = ParticleSystemSimulationSpace.Local;
            main.maxParticles = 18;

            var emission = ps.emission;
            emission.rateOverTime = _reducedMotion ? 0f : 5f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 12f;
            shape.radius = 0.16f;
            shape.position = new Vector3(0f, 0.55f, 0f);

            var colors = ps.colorOverLifetime;
            colors.enabled = true;
            colors.color = new ParticleSystem.MinMaxGradient(Gradient(
                new[]
                {
                    new GradientColorKey(UiFactory.Html("#302C2D"), 0f),
                    new GradientColorKey(UiFactory.Html("#4B515B"), 0.55f),
                    new GradientColorKey(UiFactory.Html("#687381"), 1f)
                },
                new[]
                {
                    new GradientAlphaKey(0.02f, 0f),
                    new GradientAlphaKey(0.18f, 0.24f),
                    new GradientAlphaKey(0f, 1f)
                }));

            var size = ps.sizeOverLifetime;
            size.enabled = true;
            size.size = new ParticleSystem.MinMaxCurve(
                1f,
                AnimationCurve.EaseInOut(0f, 0.38f, 1f, 1.35f));

            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Billboard;
            renderer.sharedMaterial = ParticleMaterial(
                "Niming/ParticleAlpha",
                CreateSmokeTexture());
            renderer.sortingFudge = -0.6f;
        }

        private static ParticleSystem CreateParticleSystem(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(ParticleSystem));
            go.transform.SetParent(parent, false);
            var ps = go.GetComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            ps.Play();
            return ps;
        }

        private static Gradient Gradient(
            GradientColorKey[] colors,
            GradientAlphaKey[] alpha)
        {
            var gradient = new Gradient();
            gradient.SetKeys(colors, alpha);
            return gradient;
        }

        private static Material ParticleMaterial(string shaderName, Texture2D texture)
        {
            var shader = Shader.Find(shaderName);
            if (shader == null)
            {
                shader = Shader.Find("Legacy Shaders/Particles/Additive");
            }
            var material = new Material(shader)
            {
                name = shaderName.Replace("/", "_"),
                mainTexture = texture
            };
            return material;
        }

        private static Texture2D CreateFlameTexture()
        {
            const int size = 64;
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false, true)
            {
                name = "ProceduralFlame",
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            var pixels = new Color32[size * size];
            for (int y = 0; y < size; y++)
            {
                float v = y / (size - 1f);
                float py = v * 2f - 1f;
                float width = Mathf.Lerp(0.86f, 0.10f, Mathf.Pow(v, 0.72f));
                for (int x = 0; x < size; x++)
                {
                    float px = (x / (size - 1f)) * 2f - 1f;
                    float side = Mathf.Abs(px) / Mathf.Max(width, 0.02f);
                    float vertical = Mathf.SmoothStep(0f, 1f, v * 8f)
                        * Mathf.SmoothStep(0f, 1f, (1f - v) * 5f);
                    float alpha = Mathf.Clamp01((1f - side) * 1.8f) * vertical;
                    alpha *= 0.84f + Mathf.Sin(px * 13f + py * 9f) * 0.08f;
                    byte a = (byte)(Mathf.Clamp01(alpha) * 255f);
                    pixels[y * size + x] = new Color32(255, 255, 255, a);
                }
            }
            texture.SetPixels32(pixels);
            texture.Apply(false, true);
            return texture;
        }

        private static Texture2D CreateSoftCircleTexture()
        {
            return CreateRadialTexture("SoftSpark", 0.22f);
        }

        private static Texture2D CreateSmokeTexture()
        {
            return CreateRadialTexture("SoftSmoke", 0.66f);
        }

        private static Texture2D CreateRadialTexture(string name, float softness)
        {
            const int size = 64;
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false, true)
            {
                name = name,
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            var pixels = new Color32[size * size];
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float px = x / (size - 1f) * 2f - 1f;
                    float py = y / (size - 1f) * 2f - 1f;
                    float radial = Mathf.Clamp01(1f - Mathf.Sqrt(px * px + py * py));
                    float alpha = Mathf.SmoothStep(0f, 1f, radial / Mathf.Max(softness, 0.01f));
                    byte a = (byte)(alpha * 255f);
                    pixels[y * size + x] = new Color32(255, 255, 255, a);
                }
            }
            texture.SetPixels32(pixels);
            texture.Apply(false, true);
            return texture;
        }

        private static Material CreateStandardMaterial(
            Color color,
            float smoothness,
            float metallic,
            Color? emission = null,
            float emissionStrength = 1f)
        {
            var shader = Shader.Find("Standard");
            var material = new Material(shader)
            {
                color = color,
                name = $"Material_{ColorUtility.ToHtmlStringRGB(color)}"
            };
            material.SetFloat("_Glossiness", smoothness);
            material.SetFloat("_Metallic", metallic);
            if (emission.HasValue)
            {
                material.EnableKeyword("_EMISSION");
                material.SetColor("_EmissionColor", emission.Value * emissionStrength);
            }
            return material;
        }

        private static Transform Primitive(
            PrimitiveType type,
            string name,
            Transform parent,
            Vector3 localPosition,
            Vector3 localScale,
            Material material)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            go.transform.localScale = localScale;
            Destroy(go.GetComponent<Collider>());
            go.GetComponent<Renderer>().sharedMaterial = material;
            return go.transform;
        }

        private void LateUpdate()
        {
            ApplyLayout(false);
        }

        private void ApplyLayout(bool force)
        {
            if (!force && _lastWidth == Screen.width && _lastHeight == Screen.height)
            {
                return;
            }
            _lastWidth = Screen.width;
            _lastHeight = Screen.height;
            bool mobile = Screen.height > Screen.width * 1.16f;
            PositionBackground();
            foreach (ViewportAnchor anchor in _anchors)
            {
                anchor.transform.gameObject.SetActive(!(mobile && anchor.hideOnMobile));
                Vector2 point = mobile ? anchor.mobile : anchor.desktop;
                anchor.transform.position = _camera.ViewportToWorldPoint(
                    new Vector3(point.x, point.y, anchor.depth));
                anchor.transform.rotation = Quaternion.LookRotation(
                    _camera.transform.forward,
                    _camera.transform.up);
            }
        }

        private void PositionBackground()
        {
            const float depth = 31.5f;
            float viewportHeight = 2f * depth
                * Mathf.Tan(_camera.fieldOfView * 0.5f * Mathf.Deg2Rad);
            float viewportWidth = viewportHeight * _camera.aspect;
            float textureAspect = _backdrop != null && _backdrop.height > 0
                ? _backdrop.width / (float)_backdrop.height
                : 16f / 9f;

            float width;
            float height;
            if (viewportWidth / viewportHeight > textureAspect)
            {
                width = viewportWidth;
                height = width / textureAspect;
            }
            else
            {
                height = viewportHeight;
                width = height * textureAspect;
            }
            _background.transform.position = _camera.transform.position
                + _camera.transform.forward * depth;
            _background.transform.rotation = _camera.transform.rotation;
            _background.transform.localScale = new Vector3(width, height, 1f);
        }
    }

    internal sealed class FireLightFlicker : MonoBehaviour
    {
        private Light _light;
        private float _phase;

        private void Awake()
        {
            _light = GetComponent<Light>();
            _phase = transform.position.x * 0.73f + 2.4f;
        }

        private void Update()
        {
            float t = Time.unscaledTime;
            float flicker = Mathf.Sin(t * 3.1f + _phase) * 0.56f
                + Mathf.Sin(t * 8.6f + _phase * 1.7f) * 0.29f
                + Mathf.Sin(t * 13.3f + 1.2f) * 0.15f;
            _light.intensity = 1.48f + flicker * 0.22f;
            _light.range = 4.5f + flicker * 0.12f;
        }
    }
}
