<template>
  <div class="page">
    <header class="topbar">
      <p class="tag">RESEARCH DEMO</p>
      <h1>対話型キャラクター生成Demo</h1>
    </header>

    <main class="layout">
      <!-- 左侧：聊天 -->
      <section class="chat-panel">
        <div class="chat-header">
          <h2>Chat</h2>
          <p>作りたいキャラクターについて自由に入力してください。</p>
        </div>

        <div ref="chatBody" class="chat-body">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-row"
            :class="message.role"
          >
            <div class="bubble">
              <p class="role-label">
                {{ message.role === 'user' ? 'You' : 'Agent' }}
              </p>
              <p class="message-text">{{ message.content }}</p>
            </div>
          </div>

          <div v-if="loading" class="message-row assistant">
            <div class="bubble">
              <p class="role-label">Agent</p>
              <p class="message-text">生成しています...</p>
            </div>
          </div>
        </div>

        <form class="input-area" @submit.prevent="sendMessage">
          <textarea
            v-model="inputText"
            placeholder="例：黒いロングコートを着た、冷静で強そうな女性キャラクター"
            @keydown.enter.exact.prevent="sendMessage"
          ></textarea>

          <button type="submit" :disabled="loading">
            送信
          </button>
        </form>
      </section>

      <!-- 右侧：预览 -->
      <section class="preview-panel">
        <div class="preview-card">
          <div class="preview-header">
            <h2>Preview</h2>
            <p>生成されたキャラクター</p>
          </div>

          <div class="image-area">
            <div v-if="!currentImage && !loading" class="empty-preview">
              <p>まだ画像は生成されていません</p>
              <span>左側のチャットから始めてください</span>
            </div>

            <div v-if="loading" class="loading-preview">
              <div class="loader"></div>
              <p>Generating...</p>
            </div>

            <img
              v-if="currentImage && !loading"
              :src="currentImage"
              alt="生成されたキャラクター"
              class="preview-image"
              @click="openImageModal"
            />
          </div>

          <p v-if="displayVersion > 0" class="version-text">
            Version {{ displayVersion }}
          </p>

          <div v-if="currentImage" class="image-actions">
            <button @click="openImageModal">
              拡大表示
            </button>
            <button @click="downloadCurrentImage">
              保存する
            </button>
          </div>

          <div v-if="imageHistory.length > 0" class="history-card">
            <h3>履歴</h3>

            <div class="history-list">
              <button
                v-for="item in imageHistory"
                :key="item.id"
                class="history-item"
                :class="{ active: item.version === displayVersion }"
                @click="viewHistory(item)"
              >
                <img :src="item.image" :alt="`version ${item.version}`" />
                <span>v{{ item.version }}</span>
              </button>
            </div>
          </div>

          <button class="reset-button" @click="resetCharacter">
            新しく始める
          </button>
        </div>
      </section>
    </main>

    <!-- 问卷区域 -->
    <section class="survey-section">
      <div class="survey-card">
        <div class="survey-header">
          <p class="tag">QUESTIONNAIRE</p>
          <h2>体験後アンケート</h2>
          <p>
            生成体験が終わったら、以下の質問に回答してください。
          </p>
        </div>

        <div class="survey-grid">
          <!-- Q1 -->
          <div class="survey-item full">
            <h3>Q1 画像生成AIでキャラクターを作った経験はありますか？</h3>

            <div class="choice-list">
              <label
                v-for="option in experienceOptions"
                :key="option.value"
                class="choice-option"
                :class="{ selected: survey.experience === option.value }"
              >
                <input
                  type="radio"
                  name="experience"
                  :value="option.value"
                  v-model.number="survey.experience"
                />
                <span class="choice-number">{{ option.value }}</span>
                <span>{{ option.label }}</span>
              </label>
            </div>
          </div>

          <!-- Q2-Q6 -->
          <div
            v-for="question in ratingQuestions"
            :key="question.key"
            class="survey-item"
          >
            <h3>{{ question.title }}</h3>
            <p>{{ question.description }}</p>
            <div class="rating-block">
              <div class="rating-row">
                <label
                  v-for="n in 5"
                  :key="n"
                  class="rating-option"
                  :class="{ selected: survey[question.key] === n }"
                >
                  <input
                    type="radio"
                    :name="question.key"
                    :value="n"
                    v-model.number="survey[question.key]"
                  />
                  <span>{{ n }}</span>
                </label>
              </div>
            </div>
            <div class="rating-labels">
              <span>低い</span>
              <span>高い</span>
            </div>
          </div>

          <!-- Q7-Q9 开放题 -->
          <div class="survey-item full">
            <h3>Q7 使っていて、不便だと感じた点や問題はありましたか？</h3>
            <textarea
              v-model="survey.problem"
              class="survey-textarea"
              placeholder="操作中に困った点や、分かりにくかった点があれば書いてください。"
            ></textarea>
          </div>

          <div class="survey-item full">
            <h3>Q8 改善するとしたら、どのような機能があると作りやすいと思いますか？</h3>
            <textarea
              v-model="survey.suggestion"
              class="survey-textarea"
              placeholder="追加してほしい機能や、改善してほしい点があれば書いてください。"
            ></textarea>
          </div>

          <div class="survey-item full">
            <h3>Q9 このような生成方法は、どのような場面に向いていると思いますか？</h3>
            <textarea
              v-model="survey.scene"
              class="survey-textarea"
              placeholder="このシステムが役に立ちそうな場面や使い方について、自由に書いてください。"
            ></textarea>
          </div>
        </div>

        <div class="survey-actions">
          <button @click="downloadSurveyCsv">
            回答をCSVで保存
          </button>
          <button class="secondary" @click="resetSurvey">
            アンケートをリセット
          </button>
        </div>
      </div>
    </section>

    <!-- 图片放大弹窗 -->
    <div v-if="showImageModal" class="image-modal" @click="closeImageModal">
      <div class="modal-content" @click.stop>
        <button class="modal-close" @click="closeImageModal">
          ×
        </button>

        <img :src="currentImage" alt="拡大画像" />

        <button class="modal-download" @click="downloadCurrentImage">
          この画像を保存する
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'

const inputText = ref('')
const loading = ref(false)
const currentImage = ref('')
const generationCount = ref(0)
const displayVersion = ref(0)
const chatBody = ref(null)
const imageHistory = ref([])
const showImageModal = ref(false)

const messages = ref([
  {
    id: Date.now(),
    role: 'assistant',
    content:
      'こんにちは。あなたが思う「かっこいい女性キャラクター」について教えてください。まだ曖昧でも大丈夫です。'
  }
])

const experienceOptions = [
  {
    value: 1,
    label: 'まったく使ったことがない'
  },
  {
    value: 2,
    label: '一度だけ試したことがある'
  },
  {
    value: 3,
    label: '数回使ったことがある'
  },
  {
    value: 4,
    label: '以前は使っていたが、最近はあまり使っていない'
  },
  {
    value: 5,
    label: 'よく使っていて、現在も継続的に使用している'
  }
]

const ratingQuestions = [
  {
    key: 'dialogue',
    title: 'Q2 対話だけでキャラクターのイメージを伝えることは簡単でしたか？',
    description: '言葉だけで自分のイメージを伝えやすかったかを評価してください。'
  },
  {
    key: 'match',
    title: 'Q3 キャラクターの変化を自分でコントロールできると感じましたか？',
    description: '自分の指示によってキャラクターを調整できた感覚があったかを評価してください。'
  },
  {
    key: 'consistency',
    title: 'Q4 複数回修正した後も、同じキャラクターとして維持されていましたか？',
    description: '修正を重ねても、キャラクターの一貫性が保たれていたかを評価してください。'
  },
  {
    key: 'control',
    title: 'Q5 生成されたキャラクターは、自分のイメージに合っていましたか？',
    description: '生成結果が自分の想像に近かったかを評価してください。'
  },
  {
    key: 'retry',
    title: 'Q6 機会があれば、もう一度キャラクターを作ってみたいですか？',
    description: '今後もこのような方法でキャラクターを作ってみたいかを評価してください。'
  }
]

const survey = ref({
  experience: '',
  dialogue: '',
  match: '',
  consistency: '',
  control: '',
  retry: '',
  problem: '',
  suggestion: '',
  scene: ''
})

async function sendMessage() {
  const text = inputText.value.trim()

  if (!text || loading.value) return

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: text
  })

  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const response = await fetch('http://127.0.0.1:5000/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: text
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || '生成に失敗しました')
    }

    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: data.reply
    })

    generationCount.value += 1
    displayVersion.value = generationCount.value
    currentImage.value = data.image

    imageHistory.value.unshift({
      id: Date.now() + 2,
      version: generationCount.value,
      image: data.image,
      message: text
    })
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: 'エラーが発生しました：' + error.message
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function viewHistory(item) {
  currentImage.value = item.image
  displayVersion.value = item.version
}

function openImageModal() {
  if (currentImage.value) {
    showImageModal.value = true
  }
}

function closeImageModal() {
  showImageModal.value = false
}

function downloadCurrentImage() {
  if (!currentImage.value) return

  const link = document.createElement('a')
  link.href = currentImage.value
  link.download = `character_v${displayVersion.value || 'current'}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function resetCharacter() {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/reset', {
      method: 'POST'
    })

    if (!response.ok) {
      throw new Error('リセットに失敗しました')
    }

    messages.value = [
      {
        id: Date.now(),
        role: 'assistant',
        content:
          'こんにちは。あなたが思う「かっこいい女性キャラクター」について教えてください。まだ曖昧でも大丈夫です。'
      }
    ]

    currentImage.value = ''
    generationCount.value = 0
    displayVersion.value = 0
    imageHistory.value = []
    inputText.value = ''
    showImageModal.value = false

    await nextTick()
    if (chatBody.value) {
      chatBody.value.scrollTop = 0
    }
  } catch (error) {
    console.error(error)
    alert('リセットに失敗しました：' + error.message)
  }
}

function resetSurvey() {
  survey.value = {
    experience: '',
    dialogue: '',
    match: '',
    consistency: '',
    control: '',
    retry: '',
    problem: '',
    suggestion: '',
    scene: ''
  }
}

function escapeCsv(value) {
  const text = String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

function downloadSurveyCsv() {
  const now = new Date().toISOString()

  const latestUserMessages = messages.value
    .filter((message) => message.role === 'user')
    .map((message) => message.content)
    .join(' / ')

  const headers = [
    'timestamp',
    'generation_count',
    'experience',
    'dialogue',
    'match',
    'consistency',
    'control',
    'retry',
    'problem',
    'suggestion',
    'scene',
    'user_prompts'
  ]

  const row = [
    now,
    generationCount.value,
    survey.value.experience,
    survey.value.dialogue,
    survey.value.match,
    survey.value.consistency,
    survey.value.control,
    survey.value.retry,
    survey.value.problem,
    survey.value.suggestion,
    survey.value.scene,
    latestUserMessages
  ]

  const csv =
    '\uFEFF' +
    headers.map(escapeCsv).join(',') +
    '\n' +
    row.map(escapeCsv).join(',')

  const blob = new Blob([csv], {
    type: 'text/csv;charset=utf-8;'
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `character_demo_survey_${Date.now()}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function scrollToBottom() {
  await nextTick()

  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}
</script>

<style scoped>
.page {
  min-height: 100dvh;
  width: 100%;
  background:
    radial-gradient(circle at top left, rgba(120, 90, 255, 0.22), transparent 30%),
    radial-gradient(circle at bottom right, rgba(255, 90, 150, 0.14), transparent 28%),
    #0d0d12;
  color: #f5f5f7;
  padding: 24px 40px 56px;
  box-sizing: border-box;
  overflow-x: hidden;
}

.topbar {
  max-width: 1680px;
  margin: 0 auto 24px;
  text-align: center;
  padding-top: 4px;
}

.tag {
  color: #a78bfa;
  font-size: 13px;
  letter-spacing: 0.1em;
  margin: 0 0 8px;
  text-transform: uppercase;
}

h1 {
  font-size: 38px;
  line-height: 1.25;
  margin: 0;
  letter-spacing: -0.03em;
}

.subtitle {
  max-width: 760px;
  color: #b8b8c2;
  line-height: 1.8;
  margin: 12px auto 0;
  font-size: 15px;
  text-align: center;
}

.layout {
  max-width: 1680px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(520px, 0.95fr) minmax(620px, 1.05fr);
  gap: 32px;
  min-height: calc(100dvh - 170px);
  align-items: stretch;
}

.chat-panel,
.preview-card,
.survey-card {
  background: rgba(255, 255, 255, 0.075);
  border: 1px solid rgba(255, 255, 255, 0.13);
  backdrop-filter: blur(18px);
  border-radius: 30px;
  box-shadow: 0 24px 90px rgba(0, 0, 0, 0.35);
}

.chat-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 680px;
}

.chat-header {
  padding: 22px 26px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
}

.chat-header h2,
.preview-header h2 {
  font-size: 21px;
  margin: 0 0 6px;
}

.chat-header p,
.preview-header p {
  color: #9ca3af;
  margin: 0;
  font-size: 13px;
}

.chat-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.message-row {
  display: flex;
  margin-bottom: 18px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 82%;
  padding: 16px 18px;
  border-radius: 20px;
  line-height: 1.75;
}

.user .bubble {
  background: linear-gradient(135deg, #ede9fe, #c4b5fd);
  color: #111;
  border-bottom-right-radius: 6px;
}

.assistant .bubble {
  background: rgba(255, 255, 255, 0.09);
  color: #f3f4f6;
  border-bottom-left-radius: 6px;
}

.role-label {
  font-size: 12px;
  opacity: 0.65;
  margin: 0 0 6px;
  text-align: center;
}

.message-text {
  margin: 0;
  white-space: pre-wrap;
}

.input-area {
  padding: 18px;
  display: grid;
  grid-template-columns: 1fr 88px;
  gap: 12px;
  background: rgba(0, 0, 0, 0.16);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

textarea {
  height: 58px;
  resize: none;
  border: none;
  outline: none;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.09);
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
}

textarea::placeholder {
  color: #85858f;
}

.input-area button {
  border: none;
  border-radius: 18px;
  background: #f5f3ff;
  color: #111;
  font-weight: 700;
  cursor: pointer;
}

.input-area button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-panel {
  min-width: 0;
}

.preview-card {
  height: 100%;
  min-height: 680px;
  padding: 22px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.preview-header {
  margin-bottom: 16px;
  text-align: center;
}

.image-area {
  width: min(100%, 520px);
  aspect-ratio: 2 / 3;
  margin: 0 auto;
  border-radius: 24px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)),
    #18181d;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-area img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  padding: 0;
  box-sizing: border-box;
}

.preview-image {
  cursor: zoom-in;
}

.empty-preview,
.loading-preview {
  text-align: center;
  color: #a1a1aa;
}

.empty-preview p,
.loading-preview p {
  margin: 0 0 6px;
  color: #d4d4d8;
}

.empty-preview span {
  font-size: 13px;
}

.loader {
  width: 34px;
  height: 34px;
  border: 3px solid rgba(255, 255, 255, 0.18);
  border-top-color: #c4b5fd;
  border-radius: 50%;
  margin: 0 auto 14px;
  animation: spin 0.9s linear infinite;
}

.version-text {
  color: #9ca3af;
  font-size: 13px;
  margin: 10px 0 0;
  text-align: right;
}

.image-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.image-actions button,
.reset-button,
.survey-actions button {
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  padding: 9px 14px;
  cursor: pointer;
  font-size: 13px;
}

.image-actions button:hover,
.reset-button:hover,
.survey-actions button:hover {
  background: rgba(255, 255, 255, 0.18);
}

.history-card {
  margin-top: 14px;
}

.history-card h3 {
  font-size: 15px;
  margin: 0 0 10px;
  color: #d4d4d8;
  text-align: center;
}

.history-list {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.history-item {
  position: relative;
  min-width: 90px;
  height: 110px;
  border: 2px solid transparent;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  padding: 0;
  background: #222;
  flex-shrink: 0;
}

.history-item.active {
  border-color: #c4b5fd;
}

.history-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  padding: 0;
}

.history-item span {
  position: absolute;
  left: 6px;
  bottom: 6px;
  background: rgba(0, 0, 0, 0.65);
  color: white;
  font-size: 11px;
  border-radius: 999px;
  padding: 3px 8px;
}

.reset-button {
  margin-top: 12px;
  align-self: center;
}

.survey-section {
  max-width: 1680px;
  margin: 40px auto 0;
}

.survey-card {
  padding: 30px;
}

.survey-header {
  text-align: center;
  margin-bottom: 28px;
}

.survey-header h2 {
  margin: 0 0 10px;
  font-size: 28px;
}

.survey-header p {
  margin: 0;
  color: #b8b8c2;
  line-height: 1.8;
}

.survey-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.survey-item {
  background: rgba(255, 255, 255, 0.065);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 20px;
  padding: 18px;
}

.survey-item.full {
  grid-column: 1 / -1;
}

.survey-item h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.survey-item p {
  margin: 0 0 14px;
  color: #a1a1aa;
  font-size: 13px;
  line-height: 1.7;
}

.choice-list {
  display: grid;
  gap: 10px;
}

.choice-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  cursor: pointer;
  color: #f5f5f7;
}

.choice-option input {
  display: none;
}

.choice-option.selected {
  background: rgba(196, 181, 253, 0.28);
  border: 1px solid rgba(196, 181, 253, 0.7);
}

.choice-number {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  display: grid;
  place-items: center;
  font-weight: 700;
}

.choice-option.selected .choice-number {
  background: #c4b5fd;
  color: #111;
}

.rating-block {
  width: 270px;
}

.rating-row {
  display: flex;
  gap: 10px;
}

.rating-option {
  cursor: pointer;
}

.rating-option input {
  display: none;
}

.rating-option span {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  display: grid;
  place-items: center;
  color: #f5f5f7;
}

.rating-option.selected span {
  background: #c4b5fd;
  color: #111;
  font-weight: 700;
}

.rating-labels {
  width: 250px;
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  color: #9ca3af;
  font-size: 12px;
}

.survey-textarea {
  width: 100%;
  min-height: 96px;
  box-sizing: border-box;
}

.survey-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}

.survey-actions button {
  background: #f5f3ff;
  color: #111;
  font-weight: 700;
  padding: 12px 18px;
}

.survey-actions button.secondary {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.image-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.82);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.modal-content {
  position: relative;
  max-width: 92vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.modal-content img {
  max-width: 100%;
  max-height: 82vh;
  object-fit: contain;
  border-radius: 18px;
  box-shadow: 0 24px 90px rgba(0, 0, 0, 0.6);
}

.modal-close {
  position: absolute;
  top: -18px;
  right: -18px;
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 999px;
  background: #fff;
  color: #111;
  font-size: 28px;
  cursor: pointer;
  line-height: 1;
}

.modal-download {
  margin-top: 16px;
  border: none;
  border-radius: 14px;
  background: #f5f3ff;
  color: #111;
  font-weight: 700;
  padding: 12px 18px;
  cursor: pointer;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1200px) {
  .layout {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .preview-card {
    min-height: 720px;
  }

  .image-area {
    width: min(100%, 520px);
    aspect-ratio: 2 / 3;
  }

  .survey-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .page {
    padding: 18px;
  }

  h1 {
    font-size: 28px;
  }

  .subtitle {
    font-size: 14px;
  }

  .layout {
    min-height: auto;
  }

  .input-area {
    grid-template-columns: 1fr;
  }

  .bubble {
    max-width: 90%;
  }

  .image-area {
    min-height: 420px;
  }

  .survey-card {
    padding: 20px;
  }

  .rating-row {
    gap: 6px;
  }

  .rating-option span {
    width: 34px;
    height: 34px;
  }
}
</style>