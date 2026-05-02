/**
 * Vercel AI SDK integration for Kyros persistent memory.
 *
 * Requires: npm install ai @kyros/sdk
 */

import { KyrosClient } from '../client';

// Vercel AI SDK CoreMessage type (inline to avoid hard dependency)
interface CoreMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string | Array<{ type: string; text?: string }>;
}

/**
 * Extract plain text from a CoreMessage content field.
 * Handles both string content and structured content arrays.
 */
function extractText(content: CoreMessage['content']): string {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter((p) => p.type === 'text' && typeof p.text === 'string')
      .map((p) => p.text as string)
      .join(' ');
  }
  return '';
}

/**
 * Creates a middleware wrapper for Vercel AI SDK to persist conversation history to Kyros.
 *
 * Usage:
 * ```typescript
 * import { KyrosClient } from '@kyros/sdk';
 * import { withKyrosMemory } from '@kyros/sdk/integrations/vercel';
 *
 * const client = new KyrosClient({ apiKey: 'mk_live_...' });
 * const memory = withKyrosMemory(client, 'my-agent');
 *
 * // In your route handler:
 * const enrichedMessages = await memory.onLoad(messages);
 * // ... call AI ...
 * await memory.onSave(messages);
 * ```
 */
export function withKyrosMemory(client: KyrosClient, agentId: string, k = 5) {
  return {
    /**
     * Load relevant memories and inject them as a system message before the AI call.
     */
    async onLoad(messages: CoreMessage[]): Promise<CoreMessage[]> {
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage || lastMessage.role !== 'user') return messages;

      const query = extractText(lastMessage.content);
      if (!query.trim()) return messages;

      try {
        const memoryResults = await client.recall(agentId, query, { k });
        if (memoryResults.results.length === 0) return messages;

        const context = memoryResults.results.map((r) => r.content).join('\n');
        return [
          { role: 'system', content: `Past knowledge about this user:\n${context}` },
          ...messages,
        ];
      } catch {
        // Memory recall is best-effort — return original messages on failure
        return messages;
      }
    },

    /**
     * Save the latest message turn to Kyros after the AI responds.
     */
    async onSave(messages: CoreMessage[]): Promise<void> {
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage) return;
      if (lastMessage.role !== 'user' && lastMessage.role !== 'assistant') return;

      const content = extractText(lastMessage.content);
      if (!content.trim()) return;

      try {
        await client.remember(agentId, content, { role: lastMessage.role });
      } catch {
        // Best-effort — don't throw on memory storage failure
      }
    },
  };
}
