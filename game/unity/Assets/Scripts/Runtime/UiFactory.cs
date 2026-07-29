using UnityEngine;
using UnityEngine.UI;

namespace NimingDalong
{
    internal static class UiFactory
    {
        public static readonly Color Ink = Html("#0D1218");
        public static readonly Color Panel = Html("#10171F");
        public static readonly Color PanelSoft = Html("#151E28");
        public static readonly Color TextColor = Html("#F1E9DA");
        public static readonly Color Muted = Html("#A99E91");
        public static readonly Color Accent = Html("#B74335");
        public static readonly Color AccentHover = Html("#C75242");
        public static readonly Color Gold = Html("#C8A15A");
        public static readonly Color Error = Html("#E27A69");

        public static Color Html(string hex)
        {
            return ColorUtility.TryParseHtmlString(hex, out Color value) ? value : Color.white;
        }

        public static RectTransform Rect(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            return rect;
        }

        public static void Stretch(RectTransform rect)
        {
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;
        }

        public static void Place(
            RectTransform rect,
            Vector2 anchor,
            Vector2 pivot,
            Vector2 position,
            Vector2 size)
        {
            rect.anchorMin = anchor;
            rect.anchorMax = anchor;
            rect.pivot = pivot;
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
        }

        public static Image Image(
            Transform parent,
            string name,
            Color color,
            bool raycast = false)
        {
            var rect = Rect(parent, name);
            var image = rect.gameObject.AddComponent<Image>();
            image.color = color;
            image.raycastTarget = raycast;
            return image;
        }

        public static Text Text(
            Transform parent,
            string name,
            string content,
            Font font,
            int size,
            Color color,
            TextAnchor alignment = TextAnchor.MiddleLeft)
        {
            var rect = Rect(parent, name);
            var text = rect.gameObject.AddComponent<Text>();
            text.text = content;
            text.font = font;
            text.fontSize = size;
            text.color = color;
            text.alignment = alignment;
            text.supportRichText = true;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            text.raycastTarget = false;
            return text;
        }

        public static Button Button(
            Transform parent,
            string name,
            string label,
            Font font,
            bool primary)
        {
            var image = Image(
                parent,
                name,
                primary ? Accent : new Color(0.07f, 0.10f, 0.14f, 0.92f),
                true);
            var button = image.gameObject.AddComponent<Button>();
            var colors = button.colors;
            colors.normalColor = primary ? Accent : Html("#17202A");
            colors.highlightedColor = primary ? AccentHover : Html("#202B36");
            colors.pressedColor = primary ? Html("#96352B") : Html("#0D131A");
            colors.selectedColor = colors.highlightedColor;
            colors.disabledColor = new Color(0.22f, 0.24f, 0.26f, 0.62f);
            colors.colorMultiplier = 1f;
            colors.fadeDuration = 0.16f;
            button.colors = colors;

            var outline = image.gameObject.AddComponent<Outline>();
            outline.effectColor = primary
                ? new Color(0.55f, 0.18f, 0.13f, 0.54f)
                : new Color(0.55f, 0.61f, 0.67f, 0.24f);
            outline.effectDistance = new Vector2(1f, -1f);

            var text = Text(
                image.transform,
                "Label",
                label,
                font,
                17,
                primary ? TextColor : Html("#D9D0C3"),
                TextAnchor.MiddleCenter);
            Stretch(text.rectTransform);
            return button;
        }

        public static InputField Input(
            Transform parent,
            string name,
            string placeholder,
            Font font,
            bool password)
        {
            var frame = Image(parent, name, new Color(0.035f, 0.055f, 0.075f, 0.93f), true);
            var outline = frame.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(0.35f, 0.42f, 0.50f, 0.42f);
            outline.effectDistance = new Vector2(1f, -1f);

            var input = frame.gameObject.AddComponent<InputField>();
            input.contentType = password
                ? InputField.ContentType.Password
                : InputField.ContentType.Standard;
            input.lineType = InputField.LineType.SingleLine;
            input.characterLimit = 32;
            input.caretColor = AccentHover;
            input.selectionColor = new Color(0.72f, 0.28f, 0.22f, 0.45f);

            var text = Text(
                frame.transform,
                "Text",
                string.Empty,
                font,
                17,
                Html("#EEE5D8"),
                TextAnchor.MiddleLeft);
            text.rectTransform.anchorMin = Vector2.zero;
            text.rectTransform.anchorMax = Vector2.one;
            text.rectTransform.offsetMin = new Vector2(18f, 6f);
            text.rectTransform.offsetMax = new Vector2(-18f, -6f);

            var hint = Text(
                frame.transform,
                "Placeholder",
                placeholder,
                font,
                17,
                new Color(0.58f, 0.59f, 0.60f, 0.58f),
                TextAnchor.MiddleLeft);
            hint.fontStyle = FontStyle.Normal;
            hint.rectTransform.anchorMin = Vector2.zero;
            hint.rectTransform.anchorMax = Vector2.one;
            hint.rectTransform.offsetMin = new Vector2(18f, 6f);
            hint.rectTransform.offsetMax = new Vector2(-18f, -6f);

            input.textComponent = text;
            input.placeholder = hint;
            return input;
        }
    }
}
