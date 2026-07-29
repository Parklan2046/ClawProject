Shader "Niming/Cloud"
{
    Properties
    {
        _Opacity ("Opacity", Range(0,1)) = 0.16
        _Speed ("Speed", Float) = 0.02
        _Seed ("Seed", Float) = 0
    }
    SubShader
    {
        Tags
        {
            "Queue"="Transparent-20"
            "RenderType"="Transparent"
            "IgnoreProjector"="True"
        }
        Cull Off
        ZWrite Off
        Blend SrcAlpha OneMinusSrcAlpha
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            float _Opacity;
            float _Speed;
            float _Seed;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            float hash21(float2 p)
            {
                p = frac(p * float2(123.34, 456.21));
                p += dot(p, p + 45.32);
                return frac(p.x * p.y);
            }

            float noise(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(
                    lerp(hash21(i), hash21(i + float2(1, 0)), f.x),
                    lerp(hash21(i + float2(0, 1)), hash21(i + 1), f.x),
                    f.y);
            }

            float fbm(float2 p)
            {
                float value = 0;
                float amplitude = 0.56;
                [unroll]
                for (int i = 0; i < 4; i++)
                {
                    value += noise(p) * amplitude;
                    p = p * 2.03 + float2(7.1, 3.7);
                    amplitude *= 0.48;
                }
                return value;
            }

            v2f vert(appdata input)
            {
                v2f output;
                output.position = UnityObjectToClipPos(input.vertex);
                output.uv = input.uv;
                return output;
            }

            fixed4 frag(v2f input) : SV_Target
            {
                float2 uv = input.uv;
                uv.x = uv.x * 3.2 + _Seed + _Time.y * _Speed;
                uv.y *= 3.6;
                float cloud = fbm(uv) * 0.72 + fbm(uv * 1.9 + 4.3) * 0.28;
                float edge = smoothstep(0.0, 0.22, input.uv.y)
                    * smoothstep(0.0, 0.22, 1.0 - input.uv.y)
                    * smoothstep(0.0, 0.16, input.uv.x)
                    * smoothstep(0.0, 0.16, 1.0 - input.uv.x);
                float alpha = smoothstep(0.48, 0.78, cloud) * edge * _Opacity;
                float3 moonBlue = lerp(
                    float3(0.19, 0.28, 0.38),
                    float3(0.55, 0.68, 0.80),
                    cloud);
                return float4(moonBlue, alpha);
            }
            ENDCG
        }
    }
    Fallback Off
}
