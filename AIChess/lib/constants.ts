import { LLMConfig } from './types';
import { INITIAL_FEN } from './xiangqi-engine';

export { INITIAL_FEN };

export const DEFAULT_LLM_CONFIGS: LLMConfig[] = [
  {
    id: 'deepseek',
    name: 'DeepSeek',
    provider: 'deepseek',
    baseURL: 'https://api.deepseek.com/v1',
    apiKey: '',
    model: 'deepseek-chat',
    temperature: 0.3,
    maxRetries: 3,
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    provider: 'minimax',
    baseURL: 'https://api.minimax.chat/v1',
    apiKey: '',
    model: 'MiniMax-Text-01',
    temperature: 0.3,
    maxRetries: 3,
  },
  {
    id: 'qwen',
    name: 'Qwen',
    provider: 'qwen',
    baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: '',
    model: 'qwen-max',
    temperature: 0.3,
    maxRetries: 3,
  },
  {
    id: 'moonshot',
    name: 'Moonshot',
    provider: 'moonshot',
    baseURL: 'https://api.moonshot.cn/v1',
    apiKey: '',
    model: 'moonshot-v1-8k',
    temperature: 0.3,
    maxRetries: 3,
  },
];

export const PIECE_NAMES: Record<string, string> = {
  r: '俥', n: '傌', b: '相', a: '仕', k: '帥', c: '炮', p: '兵',
  R: '車', N: '馬', B: '象', A: '士', K: '將', C: '砲', P: '卒',
};

export const SIDE_NAMES = {
  red: '紅方',
  black: '黑方',
};
