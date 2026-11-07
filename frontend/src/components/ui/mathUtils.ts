// Default trusted domains for Cloudflare R2 and local development
export const DEFAULT_ALLOWED_R2_DOMAINS = [
  'r2.cloudflarestorage.com',
  'localhost',
  '127.0.0.1',
];

export const isAllowedImageSource = (
  src?: string,
  allowBlobUrl = false,
  customAllowedDomains: readonly string[] = []
): boolean => {
  if (!src) return false;

  // 1. Asset UUID scheme: asset:<uuid>
  if (src.startsWith('asset:')) {
    return true;
  }

  // 2. Relative URLs (/assets/..., /api/v1/files/...)
  if (src.startsWith('/') && !src.startsWith('//')) {
    return true;
  }

  // 3. Blob URLs in editor preview
  if (allowBlobUrl && src.startsWith('blob:')) {
    return true;
  }

  // 4. Absolute HTTP/HTTPS URLs matching trusted R2 domains
  try {
    const url = new URL(src);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return false;
    }

    const allowed = [...DEFAULT_ALLOWED_R2_DOMAINS, ...customAllowedDomains];
    return allowed.some(
      (domain) => url.hostname === domain || url.hostname.endsWith(`.${domain}`)
    );
  } catch {
    return false;
  }
};

// Normalize single-line block math ($$...$$) to multiline block math for remark-math display mode
export const normalizeBlockMath = (text: string): string => {
  if (!text) return '';
  return text.replace(/(^|\n)\$\$([^\n]+?)\$\$($|\n)/g, (_, p1, p2, p3) => {
    return `${p1}$$\n${p2.trim()}\n$$${p3}`;
  });
};
