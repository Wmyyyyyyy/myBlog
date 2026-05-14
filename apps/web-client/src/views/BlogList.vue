<template>
  <div class="blog-list-page">
    <div class="blog-hero">
      <div class="blog-hero-inner">
        <h1>探索智慧的宁静角落</h1>
        <p>在这里，每一次阅读都是一次与心灵的对话。静下心来，开启智慧之门。</p>
        <div class="blog-hero-search">
          <svg class="blog-hero-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="搜索文章..." v-model="searchKeyword" @keyup.enter="handleSearch" />
        </div>
      </div>
    </div>

    <main class="blog-content">
      <div class="blog-layout">
        <div class="blog-cards">
          <article
            v-for="blog in blogStore.blogs"
            :key="blog.id"
            class="blog-card"
            @click="$router.push(`/blogs/${blog.id}`)"
          >
            <div class="blog-card-cover-placeholder" v-if="!blog.cover_image">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
              </svg>
            </div>
            <div class="blog-card-body">
              <div class="blog-card-meta">
                <span class="blog-card-tag" v-if="blog.category">{{ blog.category }}</span>
                <span class="blog-card-date">{{ formatDate(blog.created_at) }}</span>
              </div>
              <h2 class="blog-card-title">{{ blog.title }}</h2>
              <p class="blog-card-excerpt">{{ blog.excerpt || blog.content?.substring(0, 100) }}</p>
              <div class="blog-card-footer">
                <span class="blog-card-author">{{ blog.author_username }}</span>
                <div class="blog-card-stats">
                  <span>{{ blog.view_count }} 阅读</span>
                  <span>{{ blog.like_count }} 点赞</span>
                </div>
              </div>
            </div>
          </article>
        </div>

        <aside class="blog-sidebar">
          <button class="btn btn-primary write-btn" @click="$router.push('/blogs/new')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            写文章
          </button>

          <div class="sidebar-card">
            <div class="sidebar-card-title">分类浏览</div>
            <div class="sidebar-tag-list">
              <span class="sidebar-tag active">全部</span>
              <span class="sidebar-tag">心灵成长</span>
              <span class="sidebar-tag">读书笔记</span>
              <span class="sidebar-tag">百日筑基</span>
              <span class="sidebar-tag">禅意生活</span>
              <span class="sidebar-tag">诗词鉴赏</span>
            </div>
          </div>

          <div class="sidebar-card">
            <div class="sidebar-card-title">关于本站</div>
            <p style="font-size:13px;color:#6B7D72;line-height:1.7;">
              「静心启慧」是一个专注于心灵成长与智慧分享的平台。我们相信，在忙碌的现代生活中，每个人都需要一片宁静的精神角落。
            </p>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useBlogStore } from '@/stores/blogs'

const blogStore = useBlogStore()
const searchKeyword = ref('')

onMounted(() => {
  blogStore.fetchBlogs()
})

function handleSearch() {
  blogStore.fetchBlogs({ search: searchKeyword.value })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.blog-list-page { min-height: 100vh; background: #F2F9F4; }

.blog-hero {
  background: linear-gradient(180deg, rgba(232,245,237,0.7) 0%, #F2F9F4 100%);
  padding: 64px 24px 48px;
  text-align: center;
  border-bottom: 1px solid #DDEEE5;
}

.blog-hero-inner {
  max-width: 600px;
  margin: 0 auto;
}

.blog-hero h1 {
  font-size: 36px;
  font-weight: 700;
  color: #2D3B30;
  margin-bottom: 12px;
}

.blog-hero p {
  font-size: 16px;
  color: #6B7D72;
  margin-bottom: 24px;
}

.blog-hero-search {
  display: flex;
  align-items: center;
  max-width: 400px;
  margin: 0 auto;
  background: #FFFFFF;
  border: 1px solid #DDEEE5;
  border-radius: 100px;
  padding: 12px 20px;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(45,59,48,0.06);
}

.blog-hero-search-icon {
  color: #97C9A8;
  flex-shrink: 0;
}

.blog-hero-search input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: #2D3B30;
  background: transparent;
}

.blog-hero-search input::placeholder {
  color: #97C9A8;
}

.blog-content { max-width: 1100px; margin: 0 auto; padding: 40px 24px 80px; }
.blog-layout { display: grid; grid-template-columns: 1fr 280px; gap: 40px; }

.blog-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #DDEEE5;
  overflow: hidden;
  cursor: pointer;
  transition: all 250ms ease;
  margin-bottom: 20px;
}

.blog-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(45,59,48,0.10);
}

.blog-card-cover-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #E8F0EB 0%, rgba(151,201,168,0.4) 100%);
}

.blog-card-cover-placeholder svg { width: 48px; height: 48px; color: #97C9A8; }

.blog-card-body { padding: 24px; }
.blog-card-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.blog-card-tag {
  padding: 3px 10px;
  background: #E8F5ED;
  color: #5A9672;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
}
.blog-card-date { font-size: 12px; color: #6B7D72; }
.blog-card-title {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 19px;
  font-weight: 600;
  color: #2D3B30;
  margin-bottom: 8px;
}
.blog-card-excerpt {
  font-size: 14px;
  color: #6B7D72;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.blog-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #E8F0EB;
}
.blog-card-author { font-size: 13px; font-weight: 500; color: #2D3B30; }
.blog-card-stats { display: flex; gap: 12px; font-size: 13px; color: #6B7D72; }

.blog-sidebar { position: sticky; top: 88px; }

.write-btn {
  width: 100%;
  padding: 14px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 12px rgba(90,150,114,0.30);
  margin-bottom: 20px;
}

.write-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(90,150,114,0.40);
}

.sidebar-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #DDEEE5;
  padding: 20px;
  margin-bottom: 16px;
}
.sidebar-card-title {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 15px;
  font-weight: 600;
  color: #2D3B30;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 2px solid #E8F5ED;
}
.sidebar-tag-list { display: flex; flex-wrap: wrap; gap: 8px; }
.sidebar-tag {
  padding: 5px 12px;
  border-radius: 100px;
  font-size: 13px;
  font-weight: 500;
  background: #E8F0EB;
  color: #2D3B30;
  cursor: pointer;
  transition: all 150ms ease;
  border: 1px solid transparent;
}
.sidebar-tag:hover { background: #E8F5ED; color: #5A9672; border-color: #97C9A8; }
.sidebar-tag.active { background: #5A9672; color: #fff; }
</style>
