const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');
const escapeHtml = require('escape-html');

const BLOG_DIR = path.join(__dirname, 'blogs');
const OUTPUT_FILE = path.join(__dirname, 'blog.html');

// Define hashtags per blog post filename
const hashtagMap = {
  'redefining-risk.html': ['#EmergingMarkets', '#InclusiveFinance', '#AIInfrastructure', '#MarketResilience'],
  'blog-compliance-framework.html': ['#RegulatoryCompliance', '#GovernanceTech', '#TrustByDesign', '#FintechFrameworks'],
  'blog-ai-revolution.html': ['#AITrading', '#CFDMarkets', '#MachineLearning', '#QuantFinance'],
  'blog-human-edge.html': ['#EthicalAI', '#HumanCenteredTech', '#AILeadership', '#FintechInnovation']
};

// Inject SEO metadata into each blog post
function injectSEO(fileName, html) {
  const $ = cheerio.load(html);

  if (html.includes('<!-- SEO injected by generator -->')) return html;

  $('meta[name="description"]').remove();
  $('meta[name="keywords"]').remove();
  $('link[rel="canonical"]').remove();
  $('meta[property^="og:"]').remove();
  $('meta[name^="twitter:"]').remove();

  const title = $('title').text().trim();
  const description = $('meta[name="description"]').attr('content') || 'Sans Mercantile™ blog post.';
  const rawImage = $('img').first().attr('src') || '/img/default.jpg';
  const imagePath = rawImage.startsWith('/') ? rawImage : '/' + rawImage.replace(/^\.\.\//, '');
  const safeFileName = encodeURIComponent(fileName);
  const canonical = `https://www.sansmercantile.com/blog/${safeFileName}`;
  const keywords = hashtagMap[fileName] || ['#Uncategorized'];

  // Escape content for safe HTML attribute usage
  const escapedTitle = escapeHtml(title);
  const escapedDescription = escapeHtml(description);
  const escapedImagePath = escapeHtml(imagePath);
  const escapedCanonical = escapeHtml(canonical);
  const escapedKeywords = escapeHtml(keywords.join(', '));

  const seoBlock = `
    <meta name="description" content="${escapedDescription}" />
    <link rel="canonical" href="${escapedCanonical}" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="${escapedTitle}" />
    <meta property="og:description" content="${escapedDescription}" />
    <meta property="og:image" content="https://www.sansmercantile.com${escapedImagePath}" />
    <meta property="og:url" content="${escapedCanonical}" />
    <meta property="og:site_name" content="Sans Mercantile™" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${escapedTitle}" />
    <meta name="twitter:description" content="${escapedDescription}" />
    <meta name="twitter:image" content="https://www.sansmercantile.com${escapedImagePath}" />
    <meta name="twitter:site" content="@SansMercantile" />
    <meta name="keywords" content="${escapedKeywords}" />
    <!-- SEO injected by generator -->
  `;

  $('head').append(seoBlock);
  return $.html();
}

// Read and process blog files
const blogFiles = fs.readdirSync(BLOG_DIR)
  .filter(file => file.endsWith('.html') && file !== 'post.html');

const allPosts = [];

blogFiles.forEach(file => {
  const filePath = path.join(BLOG_DIR, file);
  const html = fs.readFileSync(filePath, 'utf8');
  const updatedHtml = injectSEO(file, html);
  if (updatedHtml !== html) {
    fs.writeFileSync(filePath, updatedHtml, 'utf8');
  }

  const $ = cheerio.load(updatedHtml);
  const title = $('title').text().trim();
  const description = $('meta[name="description"]').attr('content') || '';
  const keywords = $('meta[name="keywords"]').attr('content') || '';
  const href = `/blogs/${file}`;
  const tags = keywords.split(',').map(tag => tag.trim()).filter(tag => tag.startsWith('#'));

  allPosts.push({ title, description, href, tags });
});

const uniqueTags = [...new Set(allPosts.flatMap(post => post.tags))];

// Build blog.html output
const htmlOutput = `
<!DOCTYPE html>
<html lang="en">
<head>
  <link rel="icon" type="image/svg+xml" href="img/logo.svg" />
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sans Mercantile™ | Thought Leadership</title>
  <link rel="stylesheet" href="css/style.css" />
  <meta name="description" content="Dive into Sans Mercantile's™ research, expert analysis, and thought leadership on AI-powered trading, compliance, and inclusive market development." />

  <script>
    const allPosts = ${JSON.stringify(allPosts, null, 2)};
    localStorage.setItem('sansBlogPostsData', JSON.stringify(allPosts));
  </script>
</head>
<body>
  <div id="header-placeholder"></div>

  <main role="main" class="main-wrap">
    <section class="blog-hero" data-aos="fade-up">
      <h2>Insights & Innovation: Shaping the Future of AI Finance</h2>
      <p>Dive into Sans Mercantile’s™ research, expert analysis, and thought leadership on AI-powered trading, compliance, and inclusive market development.</p>
    </section>

    <section class="blog-articles-grid" id="blogGrid" data-aos="fade-up" data-aos-delay="150"></section>

    <section class="blog-categories" data-aos="fade-up" data-aos-delay="200">
      <h3>Explore by Category</h3>
      <div class="category-tags" id="tagBar">
        ${uniqueTags.map(tag => `<a href="#" class="tag">${tag}</a>`).join('\n')}
      </div>
      <button id="seeMoreBtn" class="cta hidden">See More</button>
    </section>
  </main>

  <div id="footer-placeholder"></div>

  <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
  <script src="/js/main.js"></script>
  <script src="js/blog-navigation.js"></script>

  <script>
    document.addEventListener('DOMContentLoaded', () => {
      AOS.init();

      const blogGrid = document.querySelector('.blog-articles-grid');
      const tagBar = document.getElementById('tagBar');
      const seeMoreBtn = document.getElementById('seeMoreBtn');

      const allPosts = JSON.parse(localStorage.getItem('sansBlogPostsData') || '[]');
      let currentTag = null;

      function renderPosts(posts) {
        blogGrid.innerHTML = posts.map(post => \`
          <article class="blog-card" data-tags="\${post.tags.join(',')}">
            <h3>\${post.title}</h3>
            <p>\${post.description}</p>
            <a href="\${post.href}" class="blog-link">Read More &rarr;</a>
          </article>
        \`).join('');
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

      const blogLinks = allPosts.map(post => post.href);
      localStorage.setItem('sansBlogPosts', JSON.stringify(blogLinks));
    });
  </script>
</body>
</html>
`;

fs.writeFileSync(OUTPUT_FILE, htmlOutput, 'utf8');
console.log(`✅ blog.html generated with ${allPosts.length} posts and ${uniqueTags.length} unique tags.`);
