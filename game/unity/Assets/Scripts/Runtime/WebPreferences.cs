using System.Runtime.InteropServices;
using UnityEngine;

namespace NimingDalong
{
    internal static class WebPreferences
    {
#if UNITY_WEBGL && !UNITY_EDITOR
        [DllImport("__Internal")]
        private static extern int NimingPrefersReducedMotion();
#endif

        public static bool ReducedMotion()
        {
#if UNITY_WEBGL && !UNITY_EDITOR
            try
            {
                return NimingPrefersReducedMotion() == 1;
            }
            catch
            {
                return false;
            }
#else
            return false;
#endif
        }
    }

    internal sealed class WuxiaAmbientMotion : MonoBehaviour
    {
        public Vector3 rotationAxis = Vector3.forward;
        public float rotationAmount = 2f;
        public float rotationSpeed = 0.6f;
        public float verticalAmount = 0.04f;
        public float verticalSpeed = 0.8f;
        public float phase;

        private Quaternion _baseRotation;
        private Vector3 _basePosition;

        private void Awake()
        {
            _baseRotation = transform.localRotation;
            _basePosition = transform.localPosition;
        }

        private void Update()
        {
            float t = Time.unscaledTime;
            transform.localRotation = _baseRotation * Quaternion.AngleAxis(
                Mathf.Sin(t * rotationSpeed + phase) * rotationAmount,
                rotationAxis);
            Vector3 position = _basePosition;
            position.y += Mathf.Sin(t * verticalSpeed + phase * 1.37f) * verticalAmount;
            transform.localPosition = position;
        }
    }
}
