import "./globals.css";

export const metadata = {
  title: "MandateGuard",
  description: "Autonomous Agent Pre-Flight Authorization Gateway for PayPal Commerce",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased font-sans">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
