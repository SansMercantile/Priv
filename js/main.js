// Responsive mobile navigation toggle and dynamic menu rendering
document.addEventListener('DOMContentLoaded', function() {
  const mobileToggle = document.querySelector('.mobile-nav-toggle');
  const mobileOverlay = document.querySelector('.mobile-nav-overlay');
  const mobileInner = document.querySelector('.mobile-nav-inner');
  const header = document.querySelector('header');
  const logo = document.querySelector('.logo');
  const navLinks = [
    { href: '/index.html', label: 'Home' },
    { href: '/about.html', label: 'About' },
    { href: '/founders-vision.html', label: "Founder's Vision", sub: true },
    { href: '/social-impact.html', label: 'Social Impact', sub: true },
    { href: '/intelligence-suite.html', label: 'Intelligence Suite', sub: true },
    { href: '/governance-ethics.html', label: 'Governance & Ethics', sub: true },
    { href: '/founders-feed.html', label: "Founder's Feed", sub: true },
    { href: '/services.html', label: 'Services' },
    { href: '/platform.html', label: 'Platform' },
    { href: '/blog.html', label: 'Blog' },
    { href: '/investors.html', label: 'Investors' },
    { href: '/contact.html', label: 'Contact' },
    { href: '/careers.html', label: 'Careers' }
  ];

  function renderMobileNav() {
    if (!mobileInner) return;
    mobileInner.innerHTML = '';
    const nav = document.createElement('nav');
    nav.className = 'nav-mobile';
    nav.setAttribute('role', 'navigation');
    navLinks.forEach(link => {
      const a = document.createElement('a');
      a.href = link.href;
      a.textContent = link.sub ? '- ' + link.label : link.label;
      nav.appendChild(a);
    });
    mobileInner.appendChild(nav);
  }

  renderMobileNav();

  if (mobileToggle && mobileOverlay) {
    mobileToggle.addEventListener('click', function() {
      const expanded = mobileOverlay.getAttribute('aria-hidden') === 'false';
      mobileOverlay.setAttribute('aria-hidden', expanded ? 'true' : 'false');
      // Always show logo, never fade
      if (logo) {
        logo.style.opacity = '1';
        logo.style.transition = 'none';
      }
    });
    // Optional: close overlay when clicking outside nav
    mobileOverlay.addEventListener('click', function(e) {
      if (e.target === mobileOverlay) {
        mobileOverlay.setAttribute('aria-hidden', 'true');
      }
    });
  }
});
// js/main.js
// This script is for pages in the root directory.

function toggleLogo() {
  const wordLogoSans = document.querySelector('.logo .sans');
  const wordLogoMerc = document.querySelector('.logo .mercantile');
  const iconLogo = document.getElementById('icon-logo');

  const isIconVisible = iconLogo.classList.contains('visible');

  if (isIconVisible) {
    iconLogo.classList.remove('visible');
    iconLogo.classList.add('hidden');

    wordLogoSans.classList.remove('hidden');
    wordLogoSans.classList.add('visible');

    wordLogoMerc.classList.remove('hidden');
    wordLogoMerc.classList.add('visible');
  } else {
    iconLogo.classList.remove('hidden');
    iconLogo.classList.add('visible');

    wordLogoSans.classList.remove('visible');
    wordLogoSans.classList.add('hidden');

    wordLogoMerc.classList.remove('visible');
    wordLogoMerc.classList.add('hidden');
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const mainContent = document.querySelector('main');
  if (mainContent) {
    mainContent.classList.add('fade-in-content');
  }

  const loadComponent = (url, placeholderId) => {
    return fetch(url)
      .then(response => {
        if (!response.ok) throw new Error(`Failed to load ${url}: ${response.statusText}`);
        return response.text();
      })
      .then(data => {
        const placeholder = document.getElementById(placeholderId);
        if (placeholder) placeholder.innerHTML = data;
        else console.error(`Placeholder element with id "${placeholderId}" not found.`);
      });
  };

  const loadAllComponents = () => {
    Promise.all([
      loadComponent('header.html', 'header-placeholder'),
      loadComponent('footer.html', 'footer-placeholder')
    ]).then(() => {
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

    // Mobile nav toggle behavior
    const mobileToggle = document.querySelector('.mobile-nav-toggle');
    const mobileOverlay = document.querySelector('.mobile-nav-overlay');
    if (mobileToggle && mobileOverlay) {
      mobileToggle.addEventListener('click', () => {
        const isOpen = mobileOverlay.getAttribute('aria-hidden') === 'false';
        mobileOverlay.setAttribute('aria-hidden', String(!isOpen));
        mobileToggle.setAttribute('aria-expanded', String(!isOpen));
      });
      // close when clicking overlay background
      mobileOverlay.addEventListener('click', (e) => {
        if (e.target === mobileOverlay) {
          mobileOverlay.setAttribute('aria-hidden', 'true');
          mobileToggle.setAttribute('aria-expanded', 'false');
        }
      });
    }

    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
      const englishRegions = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU', 'en-NZ', 'en-ZA'];
      const userLang = navigator.language || navigator.userLanguage;
      if (englishRegions.some(region => userLang.startsWith(region))) {
        languageSelect.value = 'en';
      } else {
        const langPrefix = userLang.split('-')[0];
        const optionExists = languageSelect.querySelector(`option[value="${langPrefix}"]`);
        if (optionExists) languageSelect.value = langPrefix;
        else languageSelect.value = 'en';
      }

      languageSelect.addEventListener('change', (event) => {
        const selectedLanguage = event.target.value;
        const langToPage = {
          'en': 'index.html',
          'fr': 'fr.html',
          'ja': 'ja.html',
          'zh': 'zh.html',
          'sw': 'sw.html',
          'zu': 'zu.html'
        };
        const targetPage = langToPage[selectedLanguage] || 'index.html';
        if (!window.location.pathname.endsWith(targetPage)) {
          window.location.href = '/' + targetPage;
        }
      });
    }

    const overlay = document.querySelector('.hero-overlay');
    if (overlay) {
      window.addEventListener('scroll', () => {
        const triggerPoint = window.innerHeight * 0.01;
        if (window.scrollY > triggerPoint) {
          overlay.style.opacity = 1;
          if (window.scrollY > 100) {
            overlay.style.backdropFilter = 'blur(8px)';
            overlay.style.backgroundColor = 'rgba(31, 0, 0, 0.8)';
          } else {
            overlay.style.backdropFilter = 'blur(6px)';
            overlay.style.backgroundColor = 'rgba(31, 0, 0, 0.65)';
          }
        } else {
          overlay.style.opacity = 0;
        }
      });
    }

    // --- Homepage Carousel ---
    const insightGrid = document.getElementById('insight-carousel-grid');
    const toggleButtons = document.querySelectorAll('.insight-toggle button');

    const sections = {
      insights: [
        {
          title: "Redefining Risk",
          description: "How our AI engine mitigates structural volatility in underserved markets.",
          href: "blogs/redefining-risk.html",
          image: "img/township-market-aerial-view.webp"
        },
        {
          title: "Compliance Isn’t a Checkbox",
          description: "How Sans Mercantile™ approaches governance as a trust-building framework.",
          href: "blogs/blog-compliance-framework.html",
          image: "img/compliance.webp"
        },
        {
          title: "AI Revolution in CFD Trading",
          description: "Deep learning models transforming precision and profitability.",
          href: "blogs/blog-ai-revolution.html",
          image: "img/ai-predictive-analytics-data-visualization.webp"
        },
        {
          title: "The Human Edge in AI Finance",
          description: "Fusing human intuition with machine intelligence for ethical growth.",
          href: "blogs/blog-human-edge.html",
          image: "img/human-ai-edge.webp"
        }
      ],
      newsroom: [
        {
          title: "Coming soon",
          description: "More press releases will be made available soon.",
          href: "newsroom/fintech-weekly-feature.html",
          image: "img/fintech-weekly-feature.webp"
        },
        {
          title: "Coming soon",
          description: "More press releases will be made available soon.",
          href: "newsroom/global-summit-keynote.html",
          image: "img/global-summit-2025.webp"
        }
      ],
      caseStudies: [
        {
          title: "Coming soon",
          description: "Our case studies will be made available soon.",
          href: "case-studies/microfinance-inclusion.html",
          image: "img/anima-line.webp"
        },
        {
          title: "Coming soon",
          description: "Our case studies will be made available soon.",
          href: "case-studies/inventory-optimization.html",
          image: "img/inventory-optimization.webp"
        }
      ]
    };

    let currentSection = 'insights';
    let currentIndex = 0;
    let interval;

    function renderCards(section, index = 0) {
  const posts = sections[section];
  const pair = posts.slice(index, index + 2);
  insightGrid.classList.remove('fade-in');
  insightGrid.classList.add('fade-out');

  setTimeout(() => {
    insightGrid.innerHTML = pair.map(post => `
      <article class="insight-card">
        <img 
          src="${post.image || 'img/default.jpg'}" 
          alt="${post.title}" 
          class="insight-image" 
          loading="lazy"
        />
        <h4>${post.title}</h4>
        <p>${post.description}</p>
  <a href="${post.href}">Read more</a>
      </article>
    `).join('');
    insightGrid.classList.remove('fade-out');
    insightGrid.classList.add('fade-in');
  }, 300);
}

    function startCarousel() {
      clearInterval(interval);
      const posts = sections[currentSection];
      interval = setInterval(() => {
        currentIndex = (currentIndex + 2) % posts.length;
        renderCards(currentSection, currentIndex);
      }, 5000);
    }

    toggleButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        toggleButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSection = btn.dataset.section;
        currentIndex = 0;
        renderCards(currentSection, currentIndex);
        startCarousel();
      });
    });

    if (insightGrid) {
      renderCards(currentSection);
      startCarousel();
    }

    // --- Blog Index Filtering ---
    const blogGrid = document.querySelector('.blog-articles-grid');
    const tagBar = document.getElementById('tagBar');
    const seeMoreBtn = document.getElementById('seeMoreBtn');

    if (blogGrid && tagBar) {
      const allPosts = JSON.parse(localStorage.getItem('sansBlogPostsData') || '[]');
      let currentTag = null;

      function renderPosts(posts) {
        blogGrid.innerHTML = posts.map(post => `
          <article class="blog-card" data-tags="${post.tags.join(',')}">
            <h3>${post.title}</h3>
            <p>${post.description}</p>
            <a href="${post.href}" class="blog-link">Read More &rarr;</a>
          </article>
        `).join('');
      }

      function showRandomPosts() {
        const shuffled = [...allPosts].sort(() => 0.5 - Math.random());
        renderPosts(shuffled.slice(0, 4));
        seeMoreBtn.classList.add('hidden');
        currentTag = null;
      }

      function filterByTag(tag) {
        currentTag = tag;
        const filtered = allPosts.filter(post => post.tags.includes(tag));
        renderPosts(filtered.slice(0, 2));
        seeMoreBtn.classList.remove('hidden');
      }

    function showAllForTag() {
    const filtered = allPosts.filter(post => post.tags.includes(currentTag));
    renderPosts(filtered);
    seeMoreBtn.classList.add('hidden');
  }

  tagBar.addEventListener('click', e => {
    if (e.target.classList.contains('tag')) {
      e.preventDefault();
      filterByTag(e.target.textContent.trim());
    }
  });

  seeMoreBtn.addEventListener('click', showAllForTag);
  showRandomPosts();

  setInterval(() => {
    if (!currentTag) showRandomPosts();
  }, 10000);
    } 
  }; 

  loadAllComponents();
});