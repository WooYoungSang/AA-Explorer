import type { ReactNode } from 'react';

export const metadata = {
  title: 'Base AA Explorer',
  description: 'Read-only analytics dashboard scaffold for Base ERC-4337 activity.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
