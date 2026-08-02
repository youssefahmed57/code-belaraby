import Navbar from "@/components/common/Navbar";
import Footer from "@/components/common/Footer";
import { HashScrollHandler } from "@/components/common/HashScrollHandler";

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen bg-navy-900 text-white">
      <HashScrollHandler />
      <Navbar />
      <main className="flex-grow">{children}</main>
      <Footer />
    </div>
  );
}
