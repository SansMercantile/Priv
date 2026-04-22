document.addEventListener('DOMContentLoaded', () => {
  const allPosts = JSON.parse(localStorage.getItem('sansBlogPostsData') || '[]');
  const currentPage = window.location.pathname;
  const currentIndex = allPosts.findIndex(post => post.href === currentPage);

  const prevButton = document.getElementById('prevArticleBtn');
  const nextButton = document.getElementById('nextArticleBtn');

  let hasNavigated = false;

  function navigateToPost(direction) {
    if (hasNavigated || currentIndex === -1) return;
    const newIndex = currentIndex + direction;
    if (newIndex >= 0 && newIndex < allPosts.length) {
      hasNavigated = true;
      window.location.href = allPosts[newIndex].href;
    }
  }

  // Button Navigation
  if (currentIndex !== -1) {
    if (prevButton) {
      if (currentIndex === 0) {
        prevButton.style.display = 'none';
      } else {
        prevButton.classList.remove('opacity-50', 'cursor-not-allowed');
        prevButton.addEventListener('click', () => navigateToPost(-1));
      }
    }

    if (nextButton) {
      if (currentIndex === allPosts.length - 1) {
        nextButton.style.display = 'none';
      } else {
        nextButton.classList.remove('opacity-50', 'cursor-not-allowed');
        nextButton.addEventListener('click', () => navigateToPost(1));
      }
    }
  }

    // Keyboard Navigation
document.addEventListener('keydown', e => {
  if (hasNavigated) return;

  if (e.key === 'ArrowRight') {
    hasNavigated = true;
    navigateToPost(1);
  }

  if (e.key === 'ArrowLeft') {
    hasNavigated = true;
    navigateToPost(-1);
  }

  if (e.key === 'Escape') {
    hasNavigated = true;
    window.location.href = '/blog.html';
  }
});


  // Swipe Navigation
  let touchstartX = 0;
  let touchendX = 0;
  const swipeThreshold = 50;
  const swipeTarget = document.querySelector('.main-wrap') || document.body;

  if (swipeTarget) {
    swipeTarget.addEventListener('touchstart', e => {
      touchstartX = e.changedTouches[0].screenX;
    }, { passive: true });

    swipeTarget.addEventListener('touchend', e => {
      touchendX = e.changedTouches[0].screenX;
      handleSwipe();
    });
  }

  function handleSwipe() {
    if (touchendX < touchstartX - swipeThreshold) {
      navigateToPost(1);
    }
    if (touchendX > touchstartX + swipeThreshold) {
      navigateToPost(-1);
    }
  }
});