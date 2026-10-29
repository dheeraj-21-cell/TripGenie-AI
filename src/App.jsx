import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import FullScreenBackground from './components/FullScreenBackground';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import EditorialDestinations from './components/EditorialDestinations';
import MethodologySection from './components/MethodologySection';
import Footer from './components/Footer';

export default function App() {
  const [selectedDestination, setSelectedDestination] = useState(null);

  const handleDestinationSelect = (query) => {
    setSelectedDestination(query);
    const plannerEl = document.getElementById('planner');
    if (plannerEl) {
      plannerEl.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <ThemeProvider>
      <div className="min-h-screen flex flex-col relative text-content-main selection:bg-teal-500 selection:text-white transition-colors duration-250">

        {/* Full-Viewport 2-Second Cinematic Travel Photography Slideshow */}
        <FullScreenBackground />

        {/* Navigation Bar */}
        <Navbar />

        {/* Main Content Area */}
        <main className="flex-1 relative z-10">
          <HeroSection
            selectedDestination={selectedDestination}
            onDestinationSelect={handleDestinationSelect}
          />
          <EditorialDestinations onSelectDestination={handleDestinationSelect} />
          <MethodologySection />
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </ThemeProvider>
  );
}
