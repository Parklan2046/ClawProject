import OpenAI from 'openai';
import { LLMConfig, LLMResponse } from './types';

function buildSystemPrompt(fen: string, ascii: string, legalMoves: string[], side: 'red' | 'black'): string {
  return `You are a Xiangqi (Chinese Chess) grandmaster. Play strictly by the rules.

Side to move: ${side.toUpperCase()} (${side === 'red' ? 'Red moves "up" the board / smaller ranks' : 'Black moves "down" the board / larger ranks'}).

Current position FEN: ${fen}
Board (rank 9 at top is BLACK home, rank 0 at bottom is RED home; lower-case = black, UPPER-case = red):
${ascii}

Legal moves (ICCS: <fromFile><fromRank><toFile><toRank>): ${legalMoves.join(', ')}

Piece rules:
- King (k/K): 1 step orthogonal, confined to the 3x3 palace. The two kings may never face each other on the same file with no pieces between (flying general).
- Advisor (a/A): 1 step diagonal, confined to its own palace.
- Elephant (b/B): exactly 2 diagonal steps, blocked by the midpoint "elephant eye", cannot cross the river.
- Horse (n/N): L-shape (1 orthogonal + 1 diagonal). BLOCKED if the orthogonal "horse leg" square is occupied.
- Rook (r/R): slides any distance orthogonally, blocked by intervening pieces; can capture the blocker.
- Cannon (c/C): slides orthogonally like a rook for non-capture; to capture, must jump EXACTLY one intervening piece (the "screen").
- Pawn (p/P): forward 1 step only before crossing the river; after crossing, also sideways. Never backward. Cannot capture the opposing king directly (flying-general rule).

Respond with a single JSON object and nothing else, in this exact form:
{
  "move": "e3e4",
  "reasoning": "Brief 1-2 sentence explanation of the strategic idea."
}

Choose exactly one move from the legal moves list. Do not invent moves. Output JSON only.`;
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

    if (legalMoves.length === 0) {
      return { move: '', reasoning: 'No legal moves available' };
    }

    let lastError = '';
    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        const userMsg = attempt === 0
          ? 'Choose your move.'
          : `Your previous response was invalid (${lastError}). Pick a move from the legal moves list and respond with valid JSON.`;

        const completion = await this.client.chat.completions.create({
          model: this.config.model,
          temperature: this.config.temperature,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userMsg },
          ],
          response_format: { type: 'json_object' },
          max_tokens: 256,
        });

        const content = completion.choices[0]?.message?.content || '{}';
        let parsed: LLMResponse;
        try {
          parsed = JSON.parse(content);
        } catch {
          lastError = 'response was not valid JSON';
          continue;
        }

        if (!parsed.move || !legalMoves.includes(parsed.move)) {
          lastError = `move "${parsed.move}" not in legal moves`;
          continue;
        }

        return { move: parsed.move, reasoning: parsed.reasoning || '' };
      } catch (error) {
        lastError = (error as Error).message || 'API error';
        if (attempt >= this.config.maxRetries) {
          throw error;
        }
      }
    }

    return {
      move: legalMoves[0],
      reasoning: `Fallback: selected first legal move after retries (${lastError})`,
    };
  }
}
