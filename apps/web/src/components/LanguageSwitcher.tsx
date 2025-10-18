'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

type Language = 'ru' | 'kg' | 'en';

const languages = {
  ru: { name: 'Русский', flag: '🇷🇺' },
  kg: { name: 'Кыргызча', flag: '🇰🇬' },
  en: { name: 'English', flag: '🇬🇧' },
};

export function LanguageSwitcher() {
  const [currentLang, setCurrentLang] = useState<Language>('ru');
  const [isOpen, setIsOpen] = useState(false);
  
  const handleChange = (lang: Language) => {
    setCurrentLang(lang);
    setIsOpen(false);
    
    // In production, would:
    // 1. Update user preference via API
    // 2. Reload page with new language
    // 3. Store in localStorage
    
    // For now, just update state
    localStorage.setItem('language', lang);
  };
  
  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="gap-2"
      >
        <span>{languages[currentLang].flag}</span>
        <span className="hidden sm:inline">{languages[currentLang].name}</span>
        <span className="text-xs">▼</span>
      </Button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-40 bg-card border rounded-lg shadow-lg z-50">
          {Object.entries(languages).map(([code, lang]) => (
            <button
              key={code}
              onClick={() => handleChange(code as Language)}
              className={`
                w-full flex items-center gap-2 px-4 py-2
                hover:bg-accent transition-colors
                ${currentLang === code ? 'bg-accent' : ''}
              `}
            >
              <span>{lang.flag}</span>
              <span className="text-sm">{lang.name}</span>
            </button>
          ))}
        </div>
      )}
      
      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}

