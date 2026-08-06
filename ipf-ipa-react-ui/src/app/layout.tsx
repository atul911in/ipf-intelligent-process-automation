"use client";
import type { Metadata } from "next";
import "./globals.css";

// Cannot export metadata from client component - move to server
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>IPF IPA - Intelligent Process Automation</title>
        <meta name="description" content="IPF AI-powered loan origination and credit decisioning" />
        <meta name="theme-color" content="#00544E" />
      </head>
      <body style={{background:"#F4F7F6",minHeight:"100vh"}}>{children}</body>
    </html>
  );
}