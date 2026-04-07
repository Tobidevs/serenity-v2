import type { Metadata } from "next";
import { IBM_Plex_Mono, Newsreader, Nunito_Sans } from "next/font/google";
import "./globals.css";

const editorialSans = Nunito_Sans({
  variable: "--font-editorial-sans",
  subsets: ["latin"],
});

const editorialSerif = Newsreader({
  variable: "--font-editorial-serif",
  subsets: ["latin"],
});

const editorialMono = IBM_Plex_Mono({
  variable: "--font-editorial-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Serenity Agent",
  description: "Minimal one-page chat interface for the Serenity workflow",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${editorialSans.variable} ${editorialSerif.variable} ${editorialMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
