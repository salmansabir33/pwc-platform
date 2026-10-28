ARG NODE_IMAGE
ARG NGINX_IMAGE
FROM ${NODE_IMAGE} AS build
WORKDIR /src
COPY package.json package-lock.json ./
COPY apps/ngo-web/package.json apps/ngo-web/package.json
COPY apps/pwc-ops/package.json apps/pwc-ops/package.json
COPY packages/web-api/package.json packages/web-api/package.json
COPY packages/web-ui/package.json packages/web-ui/package.json
COPY packages/web-i18n/package.json packages/web-i18n/package.json
COPY packages/design-tokens/package.json packages/design-tokens/package.json
RUN npm ci --ignore-scripts
COPY apps/ngo-web apps/ngo-web
COPY apps/pwc-ops apps/pwc-ops
COPY packages packages
COPY tsconfig.json ./
ARG PORTAL
RUN test "$PORTAL" = ngo-web -o "$PORTAL" = pwc-ops && npm run build --workspace=@pwc/$PORTAL
FROM ${NGINX_IMAGE}
ARG PORTAL
COPY --from=build /src/apps/${PORTAL}/dist /srv/portal
USER 10001:10001
ENTRYPOINT ["nginx", "-c", "/etc/pwc/nginx.conf", "-g", "daemon off;"]
