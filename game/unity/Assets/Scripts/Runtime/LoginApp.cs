using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace NimingDalong
{
    public sealed class LoginApp : MonoBehaviour
    {
        private Font _sans;
        private Font _serif;
        private RectTransform _canvasRoot;
        private RectTransform _brand;
        private RectTransform _panel;
        private Image _leftShade;
        private Text _title;
        private Text _brandStatement;
        private Text _brandCaption;
        private InputField _account;
        private InputField _secret;
        private Text _error;
        private Button _enterButton;
        private Button _guestButton;
        private Button _musicButton;
        private Text _musicLabel;
        private CanvasGroup _transition;
        private Text _transitionName;
        private Text _transitionCopy;
        private AudioSource _music;
        private bool _reducedMotion;
        private bool _musicUnlocked;
        private bool _transitioning;
        private int _lastWidth;
        private int _lastHeight;

        private static Sprite _roundedSmall;
        private static Sprite _roundedLarge;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            Application.runInBackground = true;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            _reducedMotion = WebPreferences.ReducedMotion();

            LoadAssets();
            BuildCameraAndWorld();
            BuildUi();
            BuildAudio();
            ApplyLayout(true);
        }

        private void LoadAssets()
        {
            _sans = Resources.Load<Font>("Fonts/NotoSansTC-Variable");
            _serif = Resources.Load<Font>("Fonts/NotoSerifTC-Variable");
            if (_sans == null)
            {
                _sans = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            }
            if (_serif == null)
            {
                _serif = _sans;
            }
        }

        private void BuildCameraAndWorld()
        {
            var cameraObject = new GameObject("LoginCamera", typeof(Camera));
            var camera = cameraObject.GetComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = UiFactory.Html("#07101A");
            camera.fieldOfView = 52f;
            camera.nearClipPlane = 0.08f;
            camera.farClipPlane = 90f;
            camera.allowHDR = false;
            camera.allowMSAA = true;
            camera.depth = 0;
            cameraObject.transform.position = new Vector3(0f, 2.35f, 12f);
            cameraObject.transform.rotation = Quaternion.identity;
            cameraObject.tag = "MainCamera";

            Texture2D town = Resources.Load<Texture2D>("Art/town-hybrid");
            LoginEnvironment.Build(camera, town, _reducedMotion);
        }

        private void BuildUi()
        {
            EnsureEventSystem();

            var canvasObject = new GameObject(
                "LoginInterface",
                typeof(Canvas),
                typeof(CanvasScaler),
                typeof(GraphicRaycaster));
            var canvas = canvasObject.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 20;

            var scaler = canvasObject.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1440f, 900f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            _canvasRoot = UiFactory.Rect(canvasObject.transform, "SafeComposition");
            UiFactory.Stretch(_canvasRoot);

            _leftShade = UiFactory.Image(
                _canvasRoot,
                "LeftReadabilityShade",
                new Color(0.02f, 0.035f, 0.05f, 0.22f));
            UiFactory.Stretch(_leftShade.rectTransform);
            _leftShade.rectTransform.anchorMax = new Vector2(0.58f, 1f);

            BuildBrand();
            BuildLoginPanel();
            BuildTopControls();
            BuildTransition();
        }

        private void BuildBrand()
        {
            _brand = UiFactory.Rect(_canvasRoot, "Brand");

            _title = UiFactory.Text(
                _brand,
                "GameTitle",
                "逆命\n大郎",
                _serif,
                90,
                UiFactory.TextColor,
                TextAnchor.MiddleLeft);
            _title.fontStyle = FontStyle.Normal;
            _title.lineSpacing = 0.78f;
            _title.resizeTextForBestFit = true;
            _title.resizeTextMinSize = 48;
            _title.resizeTextMaxSize = 96;
            var titleOutline = _title.gameObject.AddComponent<Outline>();
            titleOutline.effectColor = new Color(0.08f, 0.025f, 0.015f, 0.92f);
            titleOutline.effectDistance = new Vector2(3f, -3f);
            UiFactory.Place(
                _title.rectTransform,
                new Vector2(0f, 1f),
                new Vector2(0f, 1f),
                Vector2.zero,
                new Vector2(335f, 290f));

            var sealImage = UiFactory.Image(
                _brand,
                "WujiSeal",
                UiFactory.Html("#A7352B"));
            Round(sealImage, false);
            UiFactory.Place(
                sealImage.rectTransform,
                new Vector2(0f, 1f),
                new Vector2(0f, 1f),
                new Vector2(350f, -112f),
                new Vector2(48f, 70f));
            var seal = UiFactory.Text(
                sealImage.transform,
                "SealText",
                "武\n記",
                _serif,
                18,
                UiFactory.Html("#F3D5B0"),
                TextAnchor.MiddleCenter);
            seal.lineSpacing = 0.82f;
            UiFactory.Stretch(seal.rectTransform);

            var brush = UiFactory.Image(
                _brand,
                "GoldBrush",
                new Color(0.79f, 0.61f, 0.30f, 0.86f));
            UiFactory.Place(
                brush.rectTransform,
                new Vector2(0f, 1f),
                new Vector2(0f, 0.5f),
                new Vector2(0f, -324f),
                new Vector2(420f, 2f));

            _brandStatement = UiFactory.Text(
                _brand,
                "BrandStatement",
                "一餅起家 · 十日改命",
                _serif,
                24,
                UiFactory.TextColor,
                TextAnchor.MiddleLeft);
            UiFactory.Place(
                _brandStatement.rectTransform,
                new Vector2(0f, 1f),
                new Vector2(0f, 1f),
                new Vector2(0f, -338f),
                new Vector2(430f, 46f));

            _brandCaption = UiFactory.Text(
                _brand,
                "BrandCaption",
                "穿越陽谷縣，重寫武大郎嘅命數。",
                _sans,
                16,
                UiFactory.Muted,
                TextAnchor.MiddleLeft);
            UiFactory.Place(
                _brandCaption.rectTransform,
                new Vector2(0f, 1f),
                new Vector2(0f, 1f),
                new Vector2(0f, -390f),
                new Vector2(470f, 34f));
        }

        private void BuildLoginPanel()
        {
            var panelImage = UiFactory.Image(
                _canvasRoot,
                "LoginPanel",
                new Color(0.055f, 0.075f, 0.10f, 0.965f),
                true);
            _panel = panelImage.rectTransform;
            Round(panelImage, true);

            var panelOutline = panelImage.gameObject.AddComponent<Outline>();
            panelOutline.effectColor = new Color(0.46f, 0.52f, 0.58f, 0.30f);
            panelOutline.effectDistance = new Vector2(1f, -1f);

            var heading = UiFactory.Text(
                _panel,
                "Heading",
                "重返陽谷縣",
                _serif,
                27,
                UiFactory.TextColor);
            PlaceTop(heading.rectTransform, 32f, 32f, 372f, 42f);

            var subheading = UiFactory.Text(
                _panel,
                "Subheading",
                "輸入名號，繼續你嘅逆命之路。",
                _sans,
                14,
                UiFactory.Muted);
            PlaceTop(subheading.rectTransform, 32f, 77f, 372f, 30f);

            var accountLabel = UiFactory.Text(
                _panel,
                "AccountLabel",
                "帳號",
                _sans,
                14,
                UiFactory.Muted);
            PlaceTop(accountLabel.rectTransform, 32f, 126f, 372f, 24f);

            _account = UiFactory.Input(
                _panel,
                "Account",
                "少俠名號",
                _sans,
                false);
            Round(_account.GetComponent<Image>(), false);
            PlaceTopStretch(_account.GetComponent<RectTransform>(), 32f, 154f, 54f);

            var secretLabel = UiFactory.Text(
                _panel,
                "SecretLabel",
                "密語",
                _sans,
                14,
                UiFactory.Muted);
            PlaceTop(secretLabel.rectTransform, 32f, 226f, 372f, 24f);

            _secret = UiFactory.Input(
                _panel,
                "Secret",
                "江湖密語",
                _sans,
                true);
            Round(_secret.GetComponent<Image>(), false);
            PlaceTopStretch(_secret.GetComponent<RectTransform>(), 32f, 254f, 54f);

            _error = UiFactory.Text(
                _panel,
                "InlineError",
                string.Empty,
                _sans,
                13,
                UiFactory.Error);
            PlaceTop(_error.rectTransform, 32f, 312f, 372f, 28f);

            _enterButton = UiFactory.Button(
                _panel,
                "EnterButton",
                "進入江湖",
                _sans,
                true);
            Round(_enterButton.GetComponent<Image>(), false);
            PlaceTopStretch(_enterButton.GetComponent<RectTransform>(), 32f, 348f, 52f);
            _enterButton.onClick.AddListener(() => Complete(false));

            _guestButton = UiFactory.Button(
                _panel,
                "GuestButton",
                "遊客試玩",
                _sans,
                false);
            Round(_guestButton.GetComponent<Image>(), false);
            PlaceTopStretch(_guestButton.GetComponent<RectTransform>(), 32f, 412f, 48f);
            _guestButton.onClick.AddListener(() => Complete(true));

            var autofill = UiFactory.Button(
                _panel,
                "Autofill",
                "填入示範",
                _sans,
                false);
            autofill.GetComponent<Image>().color = Color.clear;
            autofill.GetComponent<Outline>().enabled = false;
            autofill.transform.Find("Label").GetComponent<Text>().fontSize = 13;
            autofill.transform.Find("Label").GetComponent<Text>().color = UiFactory.Muted;
            PlaceTop(autofill.GetComponent<RectTransform>(), 120f, 470f, 96f, 30f);
            autofill.onClick.AddListener(() =>
            {
                UnlockMusic();
                _account.text = "逆命少俠";
                _secret.text = "一餅逆命";
                SetError(string.Empty);
            });

            var clear = UiFactory.Button(
                _panel,
                "Clear",
                "清除",
                _sans,
                false);
            clear.GetComponent<Image>().color = Color.clear;
            clear.GetComponent<Outline>().enabled = false;
            clear.transform.Find("Label").GetComponent<Text>().fontSize = 13;
            clear.transform.Find("Label").GetComponent<Text>().color = UiFactory.Muted;
            PlaceTop(clear.GetComponent<RectTransform>(), 220f, 470f, 72f, 30f);
            clear.onClick.AddListener(() =>
            {
                UnlockMusic();
                _account.text = string.Empty;
                _secret.text = string.Empty;
                SetError(string.Empty);
                _account.ActivateInputField();
            });

            var note = UiFactory.Text(
                _panel,
                "PreviewNote",
                "此為 Unity 登入門面預覽，帳號系統尚未接入。",
                _sans,
                12,
                new Color(0.62f, 0.60f, 0.57f, 0.72f),
                TextAnchor.MiddleCenter);
            PlaceTopStretch(note.rectTransform, 26f, 512f, 32f);

            _account.onValueChanged.AddListener(_ => SetError(string.Empty));
            _secret.onValueChanged.AddListener(_ => SetError(string.Empty));
            _secret.onEndEdit.AddListener(_ =>
            {
                if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
                {
                    Complete(false);
                }
            });
        }

        private void BuildTopControls()
        {
            _musicButton = UiFactory.Button(
                _canvasRoot,
                "MusicButton",
                "音樂 · 開",
                _sans,
                false);
            Round(_musicButton.GetComponent<Image>(), false);
            _musicLabel = _musicButton.transform.Find("Label").GetComponent<Text>();
            _musicLabel.fontSize = 13;
            UiFactory.Place(
                _musicButton.GetComponent<RectTransform>(),
                new Vector2(1f, 1f),
                new Vector2(1f, 1f),
                new Vector2(-20f, -20f),
                new Vector2(112f, 38f));
            _musicButton.onClick.AddListener(ToggleMusic);

            var build = UiFactory.Text(
                _canvasRoot,
                "BuildLabel",
                "UNITY WEB · 第一階段",
                _sans,
                11,
                new Color(0.75f, 0.70f, 0.62f, 0.62f),
                TextAnchor.MiddleLeft);
            UiFactory.Place(
                build.rectTransform,
                new Vector2(0f, 0f),
                new Vector2(0f, 0f),
                new Vector2(20f, 16f),
                new Vector2(220f, 24f));
        }

        private void BuildTransition()
        {
            var curtain = UiFactory.Image(
                _canvasRoot,
                "TransitionCurtain",
                new Color(0.018f, 0.027f, 0.038f, 0.98f),
                true);
            UiFactory.Stretch(curtain.rectTransform);
            curtain.transform.SetAsLastSibling();
            _transition = curtain.gameObject.AddComponent<CanvasGroup>();
            _transition.alpha = 0f;
            _transition.interactable = false;
            _transition.blocksRaycasts = false;

            var eyebrow = UiFactory.Text(
                curtain.transform,
                "Eyebrow",
                "命盤已開",
                _sans,
                13,
                UiFactory.Gold,
                TextAnchor.MiddleCenter);
            UiFactory.Place(
                eyebrow.rectTransform,
                new Vector2(0.5f, 0.5f),
                new Vector2(0.5f, 0.5f),
                new Vector2(0f, 98f),
                new Vector2(280f, 28f));

            _transitionName = UiFactory.Text(
                curtain.transform,
                "PlayerName",
                "少俠",
                _serif,
                44,
                UiFactory.TextColor,
                TextAnchor.MiddleCenter);
            UiFactory.Place(
                _transitionName.rectTransform,
                new Vector2(0.5f, 0.5f),
                new Vector2(0.5f, 0.5f),
                new Vector2(0f, 34f),
                new Vector2(520f, 64f));

            _transitionCopy = UiFactory.Text(
                curtain.transform,
                "TransitionCopy",
                "序章將會喺下一個 Unity 里程碑接入。",
                _sans,
                16,
                UiFactory.Muted,
                TextAnchor.MiddleCenter);
            UiFactory.Place(
                _transitionCopy.rectTransform,
                new Vector2(0.5f, 0.5f),
                new Vector2(0.5f, 0.5f),
                new Vector2(0f, -30f),
                new Vector2(540f, 44f));

            var returnButton = UiFactory.Button(
                curtain.transform,
                "ReturnButton",
                "返回登入",
                _sans,
                false);
            Round(returnButton.GetComponent<Image>(), false);
            UiFactory.Place(
                returnButton.GetComponent<RectTransform>(),
                new Vector2(0.5f, 0.5f),
                new Vector2(0.5f, 0.5f),
                new Vector2(0f, -102f),
                new Vector2(210f, 48f));
            returnButton.onClick.AddListener(() => StartCoroutine(HideTransition()));
        }

        private void BuildAudio()
        {
            _music = gameObject.AddComponent<AudioSource>();
            _music.clip = Resources.Load<AudioClip>("Audio/login-theme");
            _music.loop = true;
            _music.playOnAwake = false;
            _music.volume = 0f;
            _music.ignoreListenerPause = true;
        }

        private void Update()
        {
            ApplyLayout(false);
            if (!_musicUnlocked &&
                (Input.anyKeyDown || Input.GetMouseButtonDown(0) || Input.touchCount > 0))
            {
                UnlockMusic();
            }
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
            if (mobile)
            {
                _leftShade.enabled = false;
                UiFactory.Place(
                    _brand,
                    new Vector2(0.5f, 1f),
                    new Vector2(0.5f, 1f),
                    new Vector2(0f, -28f),
                    new Vector2(348f, 226f));
                UiFactory.Place(
                    _title.rectTransform,
                    new Vector2(0f, 1f),
                    new Vector2(0f, 1f),
                    new Vector2(16f, 0f),
                    new Vector2(178f, 150f));
                _title.fontSize = 56;
                _brandStatement.fontSize = 18;
                UiFactory.Place(
                    _brandStatement.rectTransform,
                    new Vector2(0f, 1f),
                    new Vector2(0f, 1f),
                    new Vector2(16f, -156f),
                    new Vector2(320f, 34f));
                _brandCaption.fontSize = 14;
                UiFactory.Place(
                    _brandCaption.rectTransform,
                    new Vector2(0f, 1f),
                    new Vector2(0f, 1f),
                    new Vector2(16f, -190f),
                    new Vector2(320f, 28f));
                Transform seal = _brand.Find("WujiSeal");
                seal.gameObject.SetActive(false);
                Transform brush = _brand.Find("GoldBrush");
                brush.gameObject.SetActive(false);

                float width = Mathf.Clamp(_canvasRoot.rect.width - 28f, 330f, 430f);
                UiFactory.Place(
                    _panel,
                    new Vector2(0.5f, 0f),
                    new Vector2(0.5f, 0f),
                    new Vector2(0f, 18f),
                    new Vector2(width, 564f));
            }
            else
            {
                _leftShade.enabled = true;
                UiFactory.Place(
                    _brand,
                    new Vector2(0f, 0.5f),
                    new Vector2(0f, 0.5f),
                    new Vector2(96f, 10f),
                    new Vector2(510f, 470f));
                UiFactory.Place(
                    _title.rectTransform,
                    new Vector2(0f, 1f),
                    new Vector2(0f, 1f),
                    Vector2.zero,
                    new Vector2(335f, 290f));
                _title.fontSize = 90;
                _brandStatement.fontSize = 24;
                UiFactory.Place(
                    _brandStatement.rectTransform,
                    new Vector2(0f, 1f),
                    new Vector2(0f, 1f),
                    new Vector2(0f, -338f),
                    new Vector2(430f, 46f));
                _brandCaption.fontSize = 16;
                UiFactory.Place(
                    _brandCaption.rectTransform,
                    new Vector2(0f, 1f),
                    new Vector2(0f, 1f),
                    new Vector2(0f, -390f),
                    new Vector2(470f, 34f));
                _brand.Find("WujiSeal").gameObject.SetActive(true);
                _brand.Find("GoldBrush").gameObject.SetActive(true);
                UiFactory.Place(
                    _panel,
                    new Vector2(1f, 0.5f),
                    new Vector2(1f, 0.5f),
                    new Vector2(-108f, 0f),
                    new Vector2(432f, 568f));
            }
        }

        private void Complete(bool guest)
        {
            UnlockMusic();
            if (_transitioning)
            {
                return;
            }

            string account = _account.text.Trim();
            if (!guest)
            {
                if (account.Length < 2)
                {
                    SetError("請輸入至少兩個字嘅少俠名號。");
                    _account.ActivateInputField();
                    return;
                }
                if (_secret.text.Length < 2)
                {
                    SetError("請輸入江湖密語。");
                    _secret.ActivateInputField();
                    return;
                }
            }

            string playerName = guest ? "遊客少俠" : account;
            PlayerPrefs.SetString("niming.player_name", playerName);
            PlayerPrefs.SetInt("niming.guest", guest ? 1 : 0);
            PlayerPrefs.Save();
            _transitionName.text = playerName;
            _transitionCopy.text = guest
                ? "遊客命盤已建立。序章將會喺下一個 Unity 里程碑接入。"
                : "名號已記入命盤。序章將會喺下一個 Unity 里程碑接入。";
            StartCoroutine(ShowTransition());
        }

        private IEnumerator ShowTransition()
        {
            _transitioning = true;
            SetFormInteractable(false);
            _transition.blocksRaycasts = true;
            if (_reducedMotion)
            {
                _transition.alpha = 1f;
            }
            else
            {
                float elapsed = 0f;
                while (elapsed < 0.52f)
                {
                    elapsed += Time.unscaledDeltaTime;
                    float progress = Mathf.Clamp01(elapsed / 0.52f);
                    _transition.alpha = Mathf.SmoothStep(0f, 1f, progress);
                    yield return null;
                }
            }
            _transition.alpha = 1f;
            _transition.interactable = true;
        }

        private IEnumerator HideTransition()
        {
            _transition.interactable = false;
            if (_reducedMotion)
            {
                _transition.alpha = 0f;
            }
            else
            {
                float elapsed = 0f;
                while (elapsed < 0.34f)
                {
                    elapsed += Time.unscaledDeltaTime;
                    float progress = Mathf.Clamp01(elapsed / 0.34f);
                    _transition.alpha = Mathf.SmoothStep(1f, 0f, progress);
                    yield return null;
                }
            }
            _transition.alpha = 0f;
            _transition.blocksRaycasts = false;
            _transitioning = false;
            SetFormInteractable(true);
        }

        private void SetFormInteractable(bool value)
        {
            _account.interactable = value;
            _secret.interactable = value;
            _enterButton.interactable = value;
            _guestButton.interactable = value;
        }

        private void SetError(string message)
        {
            _error.text = message;
        }

        private void ToggleMusic()
        {
            if (!_musicUnlocked)
            {
                UnlockMusic();
                return;
            }
            if (_music != null && _music.isPlaying)
            {
                _music.Pause();
                _musicLabel.text = "音樂 · 關";
            }
            else if (_music != null && _music.clip != null)
            {
                _music.UnPause();
                if (!_music.isPlaying)
                {
                    _music.Play();
                }
                _music.volume = 0.32f;
                _musicLabel.text = "音樂 · 開";
            }
        }

        private void UnlockMusic()
        {
            if (_musicUnlocked)
            {
                return;
            }
            _musicUnlocked = true;
            if (_music == null || _music.clip == null)
            {
                _musicLabel.text = "音樂 · 無";
                return;
            }
            _music.Play();
            if (_reducedMotion)
            {
                _music.volume = 0.32f;
            }
            else
            {
                StartCoroutine(FadeMusicIn());
            }
            _musicLabel.text = "音樂 · 開";
        }

        private IEnumerator FadeMusicIn()
        {
            float elapsed = 0f;
            while (elapsed < 1.6f)
            {
                elapsed += Time.unscaledDeltaTime;
                _music.volume = Mathf.Lerp(0f, 0.32f, Mathf.Clamp01(elapsed / 1.6f));
                yield return null;
            }
            _music.volume = 0.32f;
        }

        private static void EnsureEventSystem()
        {
            if (FindFirstObjectByType<EventSystem>() != null)
            {
                return;
            }
            new GameObject(
                "EventSystem",
                typeof(EventSystem),
                typeof(StandaloneInputModule));
        }

        private static void PlaceTop(
            RectTransform rect,
            float left,
            float top,
            float width,
            float height)
        {
            UiFactory.Place(
                rect,
                new Vector2(0f, 1f),
                new Vector2(0f, 1f),
                new Vector2(left, -top),
                new Vector2(width, height));
        }

        private static void PlaceTopStretch(
            RectTransform rect,
            float horizontal,
            float top,
            float height)
        {
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(1f, 1f);
            rect.pivot = new Vector2(0.5f, 1f);
            rect.anchoredPosition = new Vector2(0f, -top);
            rect.sizeDelta = new Vector2(-horizontal * 2f, height);
        }

        private static void Round(Image image, bool large)
        {
            image.sprite = large
                ? _roundedLarge ??= CreateRoundedSprite(18f)
                : _roundedSmall ??= CreateRoundedSprite(10f);
            image.type = Image.Type.Sliced;
        }

        private static Sprite CreateRoundedSprite(float radius)
        {
            const int size = 64;
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false, true)
            {
                name = $"RoundedRect_{radius}",
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            var pixels = new Color32[size * size];
            float edge = radius;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float qx = Mathf.Max(Mathf.Abs(x - 31.5f) - (31.5f - edge), 0f);
                    float qy = Mathf.Max(Mathf.Abs(y - 31.5f) - (31.5f - edge), 0f);
                    float distance = Mathf.Sqrt(qx * qx + qy * qy);
                    float alpha = Mathf.Clamp01(edge - distance + 0.75f);
                    pixels[y * size + x] = new Color32(255, 255, 255, (byte)(alpha * 255f));
                }
            }
            texture.SetPixels32(pixels);
            texture.Apply(false, true);
            return Sprite.Create(
                texture,
                new Rect(0f, 0f, size, size),
                new Vector2(0.5f, 0.5f),
                100f,
                0,
                SpriteMeshType.FullRect,
                new Vector4(radius, radius, radius, radius));
        }
    }
}
