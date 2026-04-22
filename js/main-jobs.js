// js/main-jobs.js
// This script is for nested pages (blogs, jobs).
document.addEventListener("DOMContentLoaded", function() {
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in-content');
        mainContent.style.opacity = '0'; // Hide main content initially
    }

  const articlesData = [
    {
      id: 'redefining-risk',
      title: 'Redefining Risk: Why Township Markets Deserve Better Infrastructure',
      path: 'blogs/redefining-risk.html',
      categories: ['EmergingMarkets', 'MarketIntelligence']
    },
    {
      id: 'compliance-framework',
      title: 'Compliance Isn’t a Checkbox. It’s a Framework.',
      path: 'blogs/blog-compliance-framework.html',
      categories: ['RegulatoryCompliance', 'FintechInnovation']
    },
    {
      id: 'ai-revolution',
      title: 'The AI Revolution in CFD Trading: Precision & Profitability',
      path: 'blogs/blog-ai-revolution.html',
      categories: ['AITrading', 'FintechInnovation', 'MarketIntelligence']
    },
    {
      id: 'human-edge',
      title: 'Beyond Algorithms: The Human Edge in AI-Driven Finance',
      path: 'blogs/blog-human-edge.html',
      categories: ['AITrading', 'FintechInnovation', 'MarketIntelligence']
    }
  ];

  const loadComponent = (url, placeholderId) => {
    return fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Failed to load ${url}: ${response.statusText}`);
        }
        return response.text();
      })
      .then(data => {
        const placeholder = document.getElementById(placeholderId);
        if (placeholder) {
          placeholder.innerHTML = data;
        } else {
          console.error(`Placeholder element with id "${placeholderId}" not found.`);
        }
      });
  };

  const loadAllComponents = () => {
      const currentPathname = window.location.pathname;
      const isArticlePage = currentPathname.includes('/blogs/') && currentPathname.endsWith('.html');
      
      const headerPromise = loadComponent('../header.html', 'header-placeholder');
      const footerPromise = isArticlePage 
          ? loadComponent('../article-footer.html', 'footer-placeholder')
          : loadComponent('../footer.html', 'footer-placeholder');

      Promise.all([headerPromise, footerPromise]).then(() => {
          if (mainContent) {
              mainContent.style.opacity = '1';
          }
          initializePage();
      }).catch(error => {
          console.error("Error loading components:", error);
          if (mainContent) {
              mainContent.style.opacity = '1';
          }
      });
  };
  
  const initializePage = () => {
      AOS.init();

      setTimeout(() => {
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
          languageSelect.addEventListener('change', (event) => {
            const selectedLanguage = event.target.value;
            const langToPage = {
              'en': '/index.html',
              'fr': '/fr.html',
              'ja': '/ja.html',
              'zh': '/zh.html',
              'sw': '/sw.html',
              'zu': '/zu.html'
              // Add more mappings as you add more landing pages
            };
            const targetPage = langToPage[selectedLanguage] || '/index.html';
            window.location.href = targetPage;
          });
        }
      }, 500);

      if (document.querySelector('.hero-overlay')) {
          // Hero overlay logic here...
      }

      const currentArticleId = document.body.dataset.articleId;
      if (currentArticleId) {
          // Article navigation logic here...
      }
  };

  loadAllComponents();
});

