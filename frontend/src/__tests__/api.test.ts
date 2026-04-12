import { api } from '../lib/api';

describe('API client', () => {
  it('exports expected methods', () => {
    expect(api.userops).toBeDefined();
    expect(api.stats).toBeDefined();
    expect(api.paymasters).toBeDefined();
    expect(api.smartAccounts).toBeDefined();
    expect(api.health).toBeDefined();
  });
});
