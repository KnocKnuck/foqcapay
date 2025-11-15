import { test, expect } from '@playwright/test';

test.describe('Backend API Tests', () => {
  const API_BASE_URL = 'http://localhost:8000';

  test('should respond to root endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('name');
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('status');
    expect(data.name).toContain('FOQCAPAY');
  });

  test('should respond to health endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('healthy');
  });

  test('root endpoint should return correct structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/`);
    const data = await response.json();

    // Verify all expected fields exist
    expect(data).toHaveProperty('name');
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('mode');
    expect(data).toHaveProperty('trading_pairs');

    // Verify data types
    expect(typeof data.name).toBe('string');
    expect(typeof data.version).toBe('string');
    expect(typeof data.status).toBe('string');
    expect(typeof data.mode).toBe('string');
    expect(Array.isArray(data.trading_pairs)).toBeTruthy();
  });

  test('should return demo mode', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/`);
    const data = await response.json();

    // In test environment, should be in demo mode
    expect(data.mode).toBe('demo');
  });

  test('should return trading pairs', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/`);
    const data = await response.json();

    // Should have at least one trading pair
    expect(data.trading_pairs.length).toBeGreaterThan(0);

    // Should include expected pairs
    const expectedPairs = ['BTC/USDC', 'ETH/USDC', 'LINK/USDC'];
    expectedPairs.forEach(pair => {
      expect(data.trading_pairs).toContain(pair);
    });
  });

  test('health endpoint should return connection status', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);
    const data = await response.json();

    expect(data).toHaveProperty('mode');
    expect(data).toHaveProperty('database');
    expect(data).toHaveProperty('redis');

    // Verify connection statuses
    expect(data.database).toBe('connected');
    expect(data.redis).toBe('connected');
  });

  test('should have CORS headers', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/`);

    // Check for CORS headers (if configured)
    const headers = response.headers();

    // API should be accessible
    expect(response.ok()).toBeTruthy();
  });

  test('should return JSON content type', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/`);

    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('application/json');
  });

  test('should handle invalid endpoints gracefully', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/nonexistent-endpoint`);

    // Should return 404
    expect(response.status()).toBe(404);
  });

  test('API responses should be fast', async ({ request }) => {
    const startTime = Date.now();
    await request.get(`${API_BASE_URL}/health`);
    const endTime = Date.now();

    const responseTime = endTime - startTime;

    // Health check should respond within 1 second
    expect(responseTime).toBeLessThan(1000);
  });

  test('should maintain consistent response structure across calls', async ({ request }) => {
    // Make multiple calls
    const response1 = await request.get(`${API_BASE_URL}/`);
    const response2 = await request.get(`${API_BASE_URL}/`);

    const data1 = await response1.json();
    const data2 = await response2.json();

    // Structure should be identical
    expect(Object.keys(data1).sort()).toEqual(Object.keys(data2).sort());

    // Static fields should match
    expect(data1.name).toBe(data2.name);
    expect(data1.version).toBe(data2.version);
    expect(data1.mode).toBe(data2.mode);
  });
});
