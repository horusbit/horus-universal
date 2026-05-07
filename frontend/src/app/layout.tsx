import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HORUS Universal",
  description: "Tu orquestador personal de IA multi-modelo — 9 agentes especializados",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: "/icon-192.png",
    shortcut: "/icon-192.png",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "HORUS",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    title: "HORUS Universal",
    description: "Orquestador Personal de IA Multi-Modelo",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0f",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <head>
        {/* Prevenir zoom en iOS al hacer tap en inputs */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="HORUS" />
      </head>
      <body className={`${inter.className} bg-[#0a0a0f] text-[#e2e8f0] min-h-screen`}>
        {children}
        {/* Registro del Service Worker */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js', { scope: '/' })
                    .then(function(reg) {
                      console.log('[HORUS] Service Worker registrado:', reg.scope);
                    })
                    .catch(function(err) {
                      console.warn('[HORUS] Service Worker no disponible:', err);
                    });
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
