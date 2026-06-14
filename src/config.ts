import rawCfg from '../config/test.config.json';

export type PortalName = 'admin' | 'partner' | 'customer';
export type AccountName = 'portalAdmin' | 'noPermAdmin' | 'partner' | 'customerIndividual' | 'customerCompany';

const ACCOUNT_PORTAL_MAP: Record<AccountName, PortalName> = {
  portalAdmin:        'admin',
  noPermAdmin:        'admin',
  partner:            'partner',
  customerIndividual: 'customer',
  customerCompany:    'customer',
};

export interface PortalConfig {
  baseURL: string;
}

export interface AppConfig {
  baseURL: string;
  portals: Record<PortalName, PortalConfig>;
  timeouts: { slowEnv: boolean };
}

export interface Account {
  username: string;
  password: string;
  role: string;
}

function resolveEnvVars(value: string): string {
  return value.replace(/\$\{([^}]+)\}/g, (_, key) => process.env[key] ?? '');
}

function activeEnvCfg() {
  const envName = process.env.ENV ?? rawCfg.activeEnv;
  const envCfg = rawCfg.environments[envName as keyof typeof rawCfg.environments];
  if (!envCfg) {
    throw new Error(`Unknown environment: "${envName}". Valid: ${Object.keys(rawCfg.environments).join(', ')}`);
  }
  return envCfg;
}

export function loadConfig(portal: PortalName = 'admin'): AppConfig {
  const envCfg = activeEnvCfg();
  const activePortal = (process.env.PORTAL as PortalName) ?? portal;
  const portalCfg = envCfg[activePortal as keyof typeof envCfg] as { baseURL: string } | undefined;
  if (!portalCfg) {
    throw new Error(`Unknown portal: "${activePortal}". Valid: admin, partner, customer`);
  }

  return {
    baseURL: portalCfg.baseURL,
    portals: {
      admin:    { baseURL: envCfg.admin.baseURL },
      partner:  { baseURL: envCfg.partner.baseURL },
      customer: { baseURL: envCfg.customer.baseURL },
    },
    timeouts: rawCfg.timeouts,
  };
}

export function account(name: AccountName, portal?: PortalName): Account {
  const envCfg = activeEnvCfg();
  const resolvedPortal = portal ?? ACCOUNT_PORTAL_MAP[name];
  const portalCfg = envCfg[resolvedPortal as keyof typeof envCfg] as {
    baseURL: string;
    accounts: Record<string, { username: string; password: string; role: string }>;
  };
  const a = portalCfg.accounts[name];
  if (!a) throw new Error(`Account "${name}" not found in portal "${resolvedPortal}"`);
  return {
    username: resolveEnvVars(a.username),
    password: resolveEnvVars(a.password),
    role: a.role,
  };
}

export function portalURL(portal: PortalName): string {
  return loadConfig(portal).portals[portal].baseURL;
}

export function apiConfig() {
  const envCfg = activeEnvCfg();
  const envApi = envCfg.api as {
    baseURL: string;
    fixtures?: typeof rawCfg.api.fixtures;
  };
  return {
    ...rawCfg.api,
    baseURL: resolveEnvVars(envApi.baseURL),
    fixtures: envApi.fixtures ?? rawCfg.api.fixtures,
  };
}
