/**
 * E71 — TypeScript SDK tests.
 *
 * Tests the KyrosClient against a running local server.
 * Run with: npx jest
 */

const BASE_URL = process.env.KYROS_TEST_URL ?? 'http://localhost:8000';
const API_KEY = process.env.KYROS_TEST_API_KEY ?? 'mk_test_integration_test_key_12345';

const json = async <T>(resp: Response): Promise<T> => (await resp.json()) as T;

// We test using native fetch against the real API
// These are integration tests that require docker-compose up

describe('KyrosClient', () => {
  const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  };

  describe('Health Check', () => {
    it('should return ok without auth', async () => {
      const resp = await fetch(`${BASE_URL}/health`);
      const data = await json<{ status: string }>(resp);
      expect(resp.status).toBe(200);
      expect(data.status).toBe('ok');
    });
  });

  describe('Episodic Memory', () => {
    it('should remember and recall', async () => {
      // Remember
      const rememberResp = await fetch(`${BASE_URL}/v1/memory/episodic/remember`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-test-agent',
          content: 'TypeScript SDK test memory: user prefers VS Code',
          importance: 0.8,
        }),
      });
      expect(rememberResp.status).toBe(201);
      const rememberData = await json<{ memory_id: string }>(rememberResp);
      expect(rememberData.memory_id).toBeDefined();

      // Recall
      const recallResp = await fetch(`${BASE_URL}/v1/memory/episodic/recall`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-test-agent',
          query: 'What IDE does the user prefer?',
          k: 5,
        }),
      });
      expect(recallResp.status).toBe(200);
      const recallData = await json<{ results: unknown[] }>(recallResp);
      expect(recallData.results.length).toBeGreaterThan(0);
    });

    it('should forget a memory', async () => {
      // Store
      const resp = await fetch(`${BASE_URL}/v1/memory/episodic/remember`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-forget-agent',
          content: 'Memory to forget from TS test',
        }),
      });
      const { memory_id } = await json<{ memory_id: string }>(resp);

      // Forget
      const deleteResp = await fetch(`${BASE_URL}/v1/memory/episodic/${memory_id}`, {
        method: 'DELETE',
        headers,
      });
      expect(deleteResp.status).toBe(204);
    });
  });

  describe('Semantic Memory', () => {
    it('should store and query facts', async () => {
      // Store
      const storeResp = await fetch(`${BASE_URL}/v1/memory/semantic/facts`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-semantic-agent',
          subject: 'project_ts',
          predicate: 'language',
          object: 'TypeScript',
          confidence: 0.95,
        }),
      });
      expect(storeResp.status).toBe(201);
      const storeData = await json<{ was_contradiction: boolean }>(storeResp);
      expect(storeData.was_contradiction).toBe(false);

      // Query
      const queryResp = await fetch(`${BASE_URL}/v1/memory/semantic/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-semantic-agent',
          query: 'What language is the project using?',
          k: 3,
        }),
      });
      expect(queryResp.status).toBe(200);
    });
  });

  describe('Procedural Memory', () => {
    it('should store and match procedures', async () => {
      // Store
      const storeResp = await fetch(`${BASE_URL}/v1/memory/procedural/store`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-proc-agent',
          name: 'Run TypeScript Tests',
          description: 'Execute the TypeScript test suite with Jest',
          task_type: 'testing',
          steps: [
            { action: 'npm install' },
            { action: 'npx jest' },
          ],
        }),
      });
      expect(storeResp.status).toBe(201);

      // Match
      const matchResp = await fetch(`${BASE_URL}/v1/memory/procedural/match`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: 'ts-proc-agent',
          task_description: 'I need to run tests',
          k: 3,
        }),
      });
      expect(matchResp.status).toBe(200);
      const matchData = await json<{ results: unknown[] }>(matchResp);
      expect(matchData.results.length).toBeGreaterThan(0);
    });
  });

  describe('Admin', () => {
    it('should export memories', async () => {
      const resp = await fetch(`${BASE_URL}/v1/admin/export/ts-test-agent`, { headers });
      expect(resp.status).toBe(200);
      const data = await json<{ agent_id: string; total_memories: number }>(resp);
      expect(data.agent_id).toBe('ts-test-agent');
      expect(data.total_memories).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Authentication', () => {
    it('should reject missing API key', async () => {
      const resp = await fetch(`${BASE_URL}/v1/memory/episodic/recall`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: 'x', query: 'x', k: 1 }),
      });
      expect(resp.status).toBe(401);
    });

    it('should reject invalid API key', async () => {
      const resp = await fetch(`${BASE_URL}/v1/memory/episodic/recall`, {
        method: 'POST',
        headers: { ...headers, 'X-API-Key': 'mk_test_nonexistent' },
        body: JSON.stringify({ agent_id: 'x', query: 'x', k: 1 }),
      });
      expect(resp.status).toBe(401);
    });
  });
});
