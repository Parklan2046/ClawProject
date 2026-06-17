import OpenAI from 'openai';
import { LLMConfig, LLMResponse } from './types';

function buildSystemPrompt(fen: string, ascii: string, legalMoves: string[], side: 'red' | 'black'): string {
  return `You are a Xiangqi grandmaster. Play strictly by the rules.

Current position FEN: ${fen}
Board:
${ascii}

Legal moves (ICCS): ${legalMoves.join(', ')}

You are ${side} (${side === 'red' ? 'bottom side' : 'top side'}).

Rules:
- Horse: 1 orthogonal + 1 diagonal, blocked if horse leg is occupied
- Cannon: moves any distance orthogonally, captures by jumping exactly one piece
- Elephant: exactly 2 diagonal steps, blocked by elephant eye
- Advisor and King stay inside the palace
- Kings cannot face each other on the same file

Respond ONLY with valid JSON:
{
  "move": "e3e4",
  "reasoning": "Brief strategic reason in 1-2 sentences"
}`;
}

export class LLMPlayer {
  private client: OpenAI;
  private config: LLMConfig;

  constructor(config: LLMConfig) {
    this.config = config;
    this.client = new OpenAI({
      apiKey: config.apiKey,
      baseURL: config.baseURL,
      dangerouslyAllowBrowser: true,
    });
  }

  async getMove(
    fen: string,
    ascii: string,
    legalMoves: string[],
    side: 'red' | 'black'
  ): Promise<LLMResponse> {
    const systemPrompt = buildSystemPrompt(fen, ascii, legalMoves, side);

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        const completion = await this.client.chat.completions.create({
          model: this.config.model,
          temperature: this.config.temperature,
          messages: [
            { role: 'system', content: systemPrompt },
          ],
          response_format: { type: 'json_object' },
          max_tokens: 256,
        });

        const content = completion.choices[0]?.message?.content || '{}';
        const parsed = JSON.parse(content) as LLMResponse;

        // Validate move is in legal moves
        if (legalMoves.includes(parsed.move)) {
          return parsed;
        }

        // Invalid move - retry with feedback
        if (attempt < this.config.maxRetries) {
          continue;
        }
      } catch (error) {
        if (attempt >= this.config.maxRetries) {
          throw error;
        }
      }
    }

    // Fallback: return first legal move
    return {
      move: legalMoves[0] || 'e3e4',
      reasoning: 'Fallback: selected first legal move after retries exhausted',
    };
  }
}
