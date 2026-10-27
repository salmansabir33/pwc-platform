/** Development-only public read proxy. Never proxy authentication or private APIs. */
export function publicDirectoryProxy(target: string | undefined) {
  if (!target) return {};
  if (!/^http:\/\/127\.0\.0\.1:[0-9]{1,5}$/.test(target))
    throw new Error("Invalid public API target");
  const port = Number(target.slice(target.lastIndexOf(":") + 1));
  if (port < 1 || port > 65535) throw new Error("Invalid public API target");
  return { "^/api/v1/directory/(?:\\?.*)?$": { target, changeOrigin: true } };
}
