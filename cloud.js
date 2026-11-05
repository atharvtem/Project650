// Browser-side Cognito Hosted UI and storefront API adapter.
(function () {
  const config = window.FIELDNOTE_CONFIG;
  const SESSION_KEY = 'fieldnote_cognito_session';
  const VERIFIER_KEY = 'fieldnote_pkce_verifier';
  const ready = Boolean(config?.apiUrl && config?.userPoolClientId && config?.cognitoDomain);
  const callbackUrl = () => window.location.origin;
  const decodeJwt = token => {
    const body = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(decodeURIComponent(escape(atob(body))));
  };
  const readSession = () => {
    try { return JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null'); } catch { return null; }
  };
  const writeSession = session => sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  const currentUser = () => {
    const session = readSession();
    const idToken = session?.id_token || session?.idToken;
    if (!idToken) return null;
    try {
      const claims = decodeJwt(idToken);
      return { email: claims.email, name: claims.name || claims.given_name || claims.email?.split('@')[0], sub: claims.sub };
    } catch { return null; }
  };
  async function initialize() {
    if (!ready) return null;
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    if (code) {
      let verifier = sessionStorage.getItem(VERIFIER_KEY);
      if (!verifier) {
        try {
          const saved = JSON.parse(localStorage.getItem(VERIFIER_KEY) || 'null');
          if (saved?.expiresAt > Date.now()) verifier = saved.value;
        } catch { /* Ignore an invalid or expired temporary verifier. */ }
      }
      if (!verifier) throw new Error('Sign-in session expired. Please sign in again.');
      const response = await fetch(`${config.cognitoDomain}/oauth2/token`, {
        method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ grant_type: 'authorization_code', client_id: config.userPoolClientId, code, redirect_uri: callbackUrl(), code_verifier: verifier })
      });
      const tokens = await response.json();
      if (!response.ok) throw new Error(tokens.error_description || 'Could not complete sign-in.');
      writeSession({ ...tokens, expiresAt: Date.now() + (tokens.expires_in || 3600) * 1000 });
      sessionStorage.removeItem(VERIFIER_KEY);
      localStorage.removeItem(VERIFIER_KEY);
      window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
    }
    return currentUser();
  }
  async function login() {
    const bytes = crypto.getRandomValues(new Uint8Array(64));
    const verifier = btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
    const challenge = btoa(String.fromCharCode(...new Uint8Array(digest))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
    sessionStorage.setItem(VERIFIER_KEY, verifier);
    localStorage.setItem(VERIFIER_KEY, JSON.stringify({ value: verifier, expiresAt: Date.now() + 5 * 60 * 1000 }));
    const url = new URL(`${config.cognitoDomain}/oauth2/authorize`);
    url.search = new URLSearchParams({ client_id: config.userPoolClientId, response_type: 'code', scope: 'openid email profile', redirect_uri: callbackUrl(), code_challenge_method: 'S256', code_challenge: challenge });
    window.location.assign(url);
  }
  function logout() {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(VERIFIER_KEY);
    localStorage.removeItem(VERIFIER_KEY);
    const url = new URL(`${config.cognitoDomain}/logout`);
    url.search = new URLSearchParams({ client_id: config.userPoolClientId, logout_uri: callbackUrl() });
    window.location.assign(url);
  }
  async function accessToken() {
    let session = readSession();
    if (!session?.access_token) throw new Error('Please sign in to continue.');
    if (session.expiresAt > Date.now() + 60000) return session.access_token;
    if (!session.refresh_token) throw new Error('Your sign-in expired. Please sign in again.');
    const response = await fetch(`${config.cognitoDomain}/oauth2/token`, {
      method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'refresh_token', client_id: config.userPoolClientId, refresh_token: session.refresh_token })
    });
    const tokens = await response.json();
    if (!response.ok) { sessionStorage.removeItem(SESSION_KEY); throw new Error('Your sign-in expired. Please sign in again.'); }
    session = { ...session, ...tokens, refresh_token: session.refresh_token, expiresAt: Date.now() + (tokens.expires_in || 3600) * 1000 };
    writeSession(session);
    return session.access_token;
  }
  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (options.auth !== false) headers.set('Authorization', `Bearer ${await accessToken()}`);
    if (options.body) headers.set('content-type', 'application/json');
    const response = await fetch(`${config.apiUrl}${path}`, { ...options, headers, body: options.body ? JSON.stringify(options.body) : undefined });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
    return data;
  }
  window.FieldnoteCloud = {
    ready, config, initialize, login, logout, currentUser,
    getProducts: () => request('/products', { auth: false }),
    getCart: () => request('/cart'),
    addCartItem: (productId, quantity = 1) => request('/cart/items', { method: 'POST', body: { productId, quantity } }),
    updateCartItem: (productId, quantity) => request(`/cart/items/${encodeURIComponent(productId)}`, { method: 'PUT', body: { quantity } }),
    deleteCartItem: productId => request(`/cart/items/${encodeURIComponent(productId)}`, { method: 'DELETE' }),
    getOrders: () => request('/orders'),
    checkout: () => request('/orders', { method: 'POST', body: {} }),
    chat: question => request('/chat', { method: 'POST', body: { question } })
  };
})();
