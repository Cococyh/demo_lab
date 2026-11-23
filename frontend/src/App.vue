<template>
  <div class="app">
    <!-- ① 参加者ID -->
    <div v-if="!participantId" class="start">
      <div class="start-lang">
        <div class="lang" role="radiogroup" :aria-label="t('language')" :style="{ '--i': langIndex }">
          <span class="lang-thumb" aria-hidden="true"></span>
          <button
            v-for="item in LANGS"
            :key="item.code"
            type="button"
            role="radio"
            :aria-checked="lang === item.code"
            :class="{ on: lang === item.code }"
            @click="setLang(item.code)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
      <div class="start-card">
        <div class="logo-orb">
          <svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">
            <path d="M12 2.5l2.3 6.2 6.2 2.3-6.2 2.3L12 19.5l-2.3-6.2-6.2-2.3 6.2-2.3z" fill="currentColor" />
            <path d="M19 15.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9z" fill="currentColor" opacity=".7" />
          </svg>
        </div>
        <!-- 課題（紙の説明ページと同じ内容。オンライン参加者は説明ページがなくてもここで分かるように） -->
        <h1 class="start-title">{{ t('start.title') }}</h1>
        <p class="start-lead">{{ t('start.lead') }}</p>
        <ul v-if="startStep === 'id'" class="start-chips">
          <li v-for="chip in t('start.chips')" :key="chip">{{ chip }}</li>
        </ul>
        <p v-if="startStep === 'id'" class="start-rules">{{ t('start.rules') }}</p>
        <p v-if="startStep === 'id'" class="start-sub">
          {{ starting && !idInput ? t('start.resuming') : t('start.enterId') }}
        </p>

        <form v-if="startStep === 'id'" class="start-form" @submit.prevent="toQ1">
          <input
            v-model="idInput"
            type="text"
            maxlength="32"
            autocomplete="off"
            autofocus
          />
          <button
            type="submit"
            class="go"
            :disabled="!idInput.trim() || starting || systemStatus !== 'ok'"
          >
            {{ t('start.next') }}
          </button>
        </form>

        <!-- 質問1：作る前に聞く（紙のアンケートの質問1と同じ） -->
        <div v-else class="start-q1">
          <p class="start-q1-note">{{ t('start.q1note') }}</p>
          <p class="start-q1-title">1　{{ S.q1 }}</p>
          <div class="start-q1-opts">
            <button
              v-for="(label, i) in S.q1o"
              :key="i"
              type="button"
              :class="{ on: q1Answer === i + 1 }"
              @click="q1Answer = i + 1"
            >
              {{ label.replace('\n', '') }}
            </button>
          </div>
          <p class="start-q1-title start-q2-title">2　{{ S.p2 }}</p>
          <div class="start-q1-opts start-scale">
            <button
              v-for="(label, i) in S.p2o"
              :key="i"
              type="button"
              :class="{ on: p2Answer === i + 1 }"
              @click="p2Answer = i + 1"
            >
              <b>{{ i + 1 }}</b>{{ label }}
            </button>
          </div>
          <div class="start-q1-actions">
            <button type="button" class="start-back" @click="startStep = 'id'">{{ t('back') }}</button>
            <button
              type="button"
              class="go"
              :disabled="!q1Answer || !p2Answer || starting || systemStatus !== 'ok'"
              @click="startSession"
            >
              {{ t('start.go') }}
            </button>
          </div>
        </div>

        <p class="sys" :class="systemStatus">
          <i class="dot"></i>{{ systemStatusText }}
        </p>
        <p v-if="startError" class="start-error">{{ startErrorText }}</p>
      </div>
    </div>

    <!-- ② メイン -->
    <template v-else>
      <header class="top">
        <div class="brand">
          <span class="brand-mark">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path d="M12 2.5l2.3 6.2 6.2 2.3-6.2 2.3L12 19.5l-2.3-6.2-6.2-2.3 6.2-2.3z" fill="currentColor" />
              <path d="M19 15.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9z" fill="currentColor" opacity=".7" />
            </svg>
          </span>
        </div>

        <div class="top-right">
          <span class="pill id-pill">ID　{{ participantId }}</span>

          <div class="lang" role="radiogroup" :aria-label="t('language')" :style="{ '--i': langIndex }">
            <span class="lang-thumb" aria-hidden="true"></span>
            <button
              v-for="item in LANGS"
              :key="item.code"
              type="button"
              role="radio"
              :aria-checked="lang === item.code"
              :class="{ on: lang === item.code }"
              @click="setLang(item.code)"
            >
              {{ item.label }}
            </button>
          </div>

          <div class="timer" :class="{ warn: remainingSeconds <= 120 }" :title="t('timeLeft')">
            <svg viewBox="0 0 44 44" class="ring" aria-hidden="true">
              <circle class="ring-bg" cx="22" cy="22" r="19" />
              <circle
                class="ring-fg"
                cx="22"
                cy="22"
                r="19"
                :style="{ strokeDashoffset: ringOffset }"
              />
            </svg>
            <span class="timer-text">{{ timeText }}</span>
          </div>
        </div>
      </header>

      <Transition name="toast">
        <div v-if="timeNotice" class="toast">
          <span>{{ t(timeNotice) }}</span>
          <button type="button" :aria-label="t('close')" @click="timeNotice = ''">×</button>
        </div>
      </Transition>

      <main class="main">
        <!-- 画像ステージ -->
        <section class="stage">
          <div class="frame-wrap">
          <div class="frame" :class="{ busy: loading, has: !!currentImage }">
            <Transition name="pop" mode="out-in">
              <div v-if="loading" key="loading" class="loading">
                <div class="shimmer"></div>
                <div class="loading-center">
                  <div class="orbit"><i></i><i></i><i></i></div>
                  <p class="loading-text">{{ loadingText }}</p>
                </div>
              </div>

              <img
                v-else-if="currentImage"
                :key="displayVersion"
                :src="currentImage"
                :alt="t('image.alt')"
                class="art"
                @click="openImageModal"
              />

              <div v-else key="empty" class="empty">
                <div class="empty-orb">
                  <svg viewBox="0 0 24 24" width="40" height="40" aria-hidden="true">
<circle cx="12" cy="8.2" r="4.2" fill="currentColor" />
<path d="M3.8 21.2c.5-4.6 3.9-7.4 8.2-7.4s7.7 2.8 8.2 7.4z" fill="currentColor" />
</svg>
                </div>
                <p>{{ t('empty') }}</p>
              </div>
            </Transition>

            <span v-if="displayVersion > 0 && !loading" class="ver-badge">
              Ver. {{ displayVersion }}
              <b v-if="displayVersion === finalVersion">★</b>
            </span>

            <div
              v-if="displayVersion > 0 && baseVersion > 0 && displayVersion !== baseVersion && !loading && !restartPending"
              class="edit-note"
            >
              <span>{{ t('editNote', { v: baseVersion }) }}</span>
              <button type="button" @click="setBase">{{ t('baseSet', { v: displayVersion }) }}</button>
            </div>

            <button
              v-if="imageHistory.length > 1 && !loading"
              type="button"
              class="compare-btn"
              @click="openCompare"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                <rect x="3" y="5" width="7.5" height="14" rx="1.5" fill="none" stroke="currentColor" stroke-width="2" />
                <rect x="13.5" y="5" width="7.5" height="14" rx="1.5" fill="none" stroke="currentColor" stroke-width="2" />
              </svg>
              {{ t('compare') }}
            </button>

            <button
              v-if="currentImage && !loading"
              type="button"
              class="zoom"
              :aria-label="t('zoom')"
              @click="openImageModal"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
            </button>
          </div>

          </div>

          <!-- 画像の下：左に履歴、右に最終画像ボタン（最初から場所を確保しておき、画像がずれないようにする） -->
          <div class="under">
            <div ref="stripEl" class="strip">
              <button
                v-for="item in imageHistory"
                :key="item.id"
                type="button"
                class="thumb"
                :class="{ active: item.version === displayVersion, 'is-final': item.version === finalVersion }"
                @click="viewHistory(item)"
              >
                <img :src="item.image" :alt="`Ver. ${item.version}`" />
                <span>Ver. {{ item.version }}</span>
                <i v-if="item.version === finalVersion" class="star">★</i>
              </button>
              <div v-if="!imageHistory.length" class="thumb ghost" aria-hidden="true">
                <i></i>
                <span>Ver. 1</span>
              </div>
            </div>

            <div class="final-row">
              <button
                type="button"
                class="final"
                :class="{ chosen: !!finalVersion && finalVersion === displayVersion }"
                :disabled="!currentImage || loading"
                @click="chooseFinal"
              >
                <span v-if="!displayVersion">{{ t('finalNone') }}</span>
                <span v-else-if="finalVersion === displayVersion">{{ t('finalChosen', { v: displayVersion }) }}</span>
                <span v-else>{{ t('finalSet', { v: displayVersion }) }}</span>
              </button>
              <!-- 選ぶ前から場所を確保しておく（表示されたときに画像がずれないように） -->
              <p class="final-hint" :class="{ hidden: !finalVersion }">
                {{ t('finalHint', { v: finalVersion || 1 }) }}
              </p>
            </div>
          </div>
        </section>

        <!-- チャット -->
        <section class="chat">
          <div ref="chatBody" class="chat-body">
            <div
              v-for="message in messages"
              :key="message.id"
              class="msg"
              :class="message.role"
            >
              <p>{{ messageText(message) }}</p>
            </div>

            <div v-if="loading" class="msg assistant typing">
              <span class="dots"><i></i><i></i><i></i></span>
            </div>
          </div>

          <div v-if="restartPending && !loading" class="restart-bar">
            <span>{{ t('restartBar') }}</span>
            <button type="button" class="link-btn" @click="cancelRestart">{{ t('restartCancel') }}</button>
          </div>
          <div v-else-if="imageHistory.length && !loading" class="restart-row">
            <button type="button" class="link-btn" @click="restartDesign">
              <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">
                <path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              {{ t('restartBtn') }}
            </button>
          </div>

          <form class="composer" @submit.prevent="sendMessage">
            <textarea
              ref="composerInput"
              v-model="inputText"
              rows="2"
              :disabled="loading"
              :placeholder="t(imageHistory.length && !restartPending ? 'placeholderEdit' : 'placeholderNew')"
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button type="submit" class="send" :disabled="loading || !inputText.trim()" :aria-label="t('send')">
              <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                <path d="M3 11.5l17-8-6.5 17-3-7-7.5-2z" fill="currentColor" />
              </svg>
            </button>
          </form>

          <button type="button" class="finish" @click="finishSession">
            {{ t('finish') }}
          </button>
        </section>
      </main>
    </template>

    <!-- 終了後のお礼。オンライン参加者だけ、折りたたみを開いてアンケートに答える -->
    <Transition name="fade">
      <div v-if="thanks" class="modal">
        <div class="thanks-box" role="dialog" aria-modal="true">
          <p class="dialog-message">
            {{ thanks.final ? t('thanksFinal', { v: thanks.final }) : t('thanks') }}
          </p>
          <p class="thanks-onsite">{{ t('thanksOnsite') }}</p>

          <details class="survey" :open="surveyOpen" @toggle="surveyOpen = $event.target.open">
            <summary>{{ S.toggle }}</summary>
            <p class="survey-note">{{ S.onsite }}</p>

            <div v-if="surveyState === 'sent'" class="survey-sent">{{ S.sent }}</div>
            <form v-else class="survey-form" @submit.prevent="submitSurvey">
              <p v-if="thanks.final" class="survey-final">
                {{ S.finalLabel }}<b>Ver. {{ thanks.final }}</b>
              </p>

              <!-- 2・3：紙と同じく5段階を横に並べる -->
              <section
                v-for="q in ['qc', 'q3']"
                :key="q"
                class="q"
                :data-q="q"
                :class="{ missing: showMissing && !answered(q) }"
              >
                <h4>
                  <span class="q-no">{{ NUM[q] }}</span>{{ S[q] }}<small>{{ S.one }}</small><i class="req">{{ S.req }}</i>
                </h4>
                <div class="scale">
                  <label
                    v-for="(label, i) in S[q + 'o']"
                    :key="i"
                    class="scale-opt"
                    :class="{ on: survey[q] === i + 1 }"
                  >
                    <input v-model="survey[q]" class="vh" type="radio" :name="q" :value="i + 1" />
                    <b>{{ i + 1 }}</b>
                    <span>{{ label }}</span>
                  </label>
                </div>
              </section>

              <section class="q" data-q="q4" :class="{ missing: showMissing && !answered('q4') }">
                <h4>
                  <span class="q-no">{{ NUM.q4 }}</span>{{ S.q4 }}<small>{{ S.upTo3 }}</small><i class="req">{{ S.req }}</i>
                  <em class="count">{{ survey.q4.length }}/3</em>
                </h4>
                <div class="chips">
                  <label
                    v-for="code in Q4_CODES"
                    :key="code"
                    class="chip"
                    :class="{ on: survey.q4.includes(code), off: survey.q4.length >= 3 && !survey.q4.includes(code) }"
                  >
                    <input
                      v-model="survey.q4"
                      class="vh"
                      type="checkbox"
                      :value="code"
                      :disabled="survey.q4.length >= 3 && !survey.q4.includes(code)"
                    />
                    {{ S.q4o[code] }}
                  </label>
                </div>
                <input
                  v-if="survey.q4.includes('other')"
                  v-model="survey.q4_other"
                  class="other-input"
                  maxlength="200"
                  :placeholder="S.otherPh"
                />
              </section>

              <section class="q" data-q="q5" :class="{ missing: showMissing && !answered('q5') }">
                <h4><span class="q-no">{{ NUM.q5 }}</span>{{ S.q5 }}<small>{{ S.many }}</small><i class="req">{{ S.req }}</i></h4>
                <div v-for="group in Q5_GROUPS" :key="group.key" class="chip-group">
                  <span class="group-label">{{ S.q5g[group.key] }}</span>
                  <div class="chips">
                    <label
                      v-for="code in group.codes"
                      :key="code"
                      class="chip"
                      :class="{ on: survey.q5.includes(code) }"
                    >
                      <input v-model="survey.q5" class="vh" type="checkbox" :value="code" />
                      {{ S.q5o[code] }}
                    </label>
                  </div>
                </div>
                <input
                  v-if="survey.q5.includes('other')"
                  v-model="survey.q5_other"
                  class="other-input"
                  maxlength="200"
                  :placeholder="S.otherPh"
                />
              </section>

              <section class="q" data-q="q6" :class="{ missing: showMissing && !answered('q6') }">
                <h4><span class="q-no">{{ NUM.q6 }}</span>{{ S.q6 }}<small>{{ S.many }}</small><i class="req">{{ S.req }}</i></h4>
                <div class="chips">
                  <label
                    v-for="code in Q6_CODES"
                    :key="code"
                    class="chip"
                    :class="{ on: survey.q6.includes(code) }"
                  >
                    <input v-model="survey.q6" class="vh" type="checkbox" :value="code" />
                    {{ S.q6o[code] }}
                  </label>
                </div>
                <input
                  v-if="survey.q6.includes('other')"
                  v-model="survey.q6_other"
                  class="other-input"
                  maxlength="200"
                  :placeholder="S.otherPh"
                />
              </section>

              <section class="q">
                <h4><span class="q-no">{{ NUM.q7 }}</span>{{ S.q7 }}<small>{{ S.optional }}</small></h4>
                <textarea v-model="survey.q7" rows="3" maxlength="1000"></textarea>
              </section>

              <p v-if="surveyState === 'error'" class="survey-error">{{ surveyError }}</p>
              <button
                type="submit"
                class="dialog-ok survey-submit"
                :disabled="surveyState === 'sending'"
              >
                {{ surveyState === 'sending' ? S.sending : S.submit }}
              </button>
              <p v-if="showMissing && !surveyReady" class="survey-error">{{ S.required }}</p>
            </form>
          </details>

          <div class="dialog-actions">
            <button type="button" class="dialog-cancel" @click="closeThanks">{{ t('close') }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 確認ダイアログ -->
    <Transition name="fade">
      <div v-if="dialog" class="modal" @click="closeDialog(false)">
        <div class="dialog-box" role="dialog" aria-modal="true" @click.stop>
          <p class="dialog-message">{{ dialog.message }}</p>
          <div class="dialog-actions">
            <button
              v-if="dialog.cancelText"
              type="button"
              class="dialog-cancel"
              @click="closeDialog(false)"
            >
              {{ dialog.cancelText }}
            </button>
            <button
              type="button"
              class="dialog-ok"
              :class="{ danger: dialog.danger }"
              @click="closeDialog(true)"
            >
              {{ dialog.okText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 2つのバージョンを並べて比べる -->
    <Transition name="fade">
      <div v-if="compare" class="modal" @click="compare = null">
        <div class="compare-box" @click.stop>
          <button type="button" class="modal-close" :aria-label="t('close')" @click="compare = null">×</button>
          <div v-for="side in ['left', 'right']" :key="side" class="compare-pane">
            <img :src="imageHistory[compare[side]].image" :alt="`Ver. ${imageHistory[compare[side]].version}`" />
            <div class="compare-nav">
              <button
                type="button"
                :aria-label="t('prev')"
                :disabled="compare[side] <= 0"
                @click="compare[side] -= 1"
              >
                ‹
              </button>
              <span>
                Ver. {{ imageHistory[compare[side]].version }}
                <b v-if="imageHistory[compare[side]].version === finalVersion">★</b>
              </span>
              <button
                type="button"
                :aria-label="t('next')"
                :disabled="compare[side] >= imageHistory.length - 1"
                @click="compare[side] += 1"
              >
                ›
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 拡大 -->
    <Transition name="fade">
      <div v-if="showImageModal" class="modal" @click="closeImageModal">
        <div class="modal-box" @click.stop>
          <button type="button" class="modal-close" :aria-label="t('close')" @click="closeImageModal">×</button>
          <img :src="currentImage" :alt="t('image.zoomAlt')" />
          <button type="button" class="save" @click="downloadCurrentImage">{{ t('save') }}</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LANGS, MESSAGES } from './i18n.js'
import { Q4_CODES, Q5_GROUPS, Q6_CODES, SURVEY } from './survey.js'

// 开发时前端(5173)直连后端(5000)；正式构建后由后端托管，使用同源地址
const API_BASE =
  import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? 'http://127.0.0.1:5000' : '')
const TIME_LIMIT_SECONDS = 10 * 60
const WARNING_SECONDS = 2 * 60

// 表示言語（日本語 / 中文 / English）。ブラウザに覚えておき、再読み込みしても保つ
const LANG_KEY = 'avatar_maker_lang'
function savedLang() {
  try {
    const value = localStorage.getItem(LANG_KEY)
    return MESSAGES[value] ? value : 'ja'
  } catch (error) {
    return 'ja'
  }
}
const lang = ref(savedLang())
const langIndex = computed(() => LANGS.findIndex((item) => item.code === lang.value))

// t('key', { v: 3 })：今の言語の文言を返す（無ければ日本語、それも無ければキーそのもの）
function t(key, params = {}) {
  if (!key) return ''
  const text = MESSAGES[lang.value][key] ?? MESSAGES.ja[key] ?? key
  if (typeof text !== 'string') return text
  return text.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? ''))
}

function applyLang() {
  document.documentElement.lang = lang.value === 'zh' ? 'zh-CN' : lang.value
}
applyLang()

function setLang(code, { log = true } = {}) {
  if (!MESSAGES[code] || code === lang.value) return
  lang.value = code
  applyLang()
  try {
    localStorage.setItem(LANG_KEY, code)
  } catch (error) {
    /* 保存できない環境でも切り替え自体はできる */
  }
  // 実験中の切り替えはログに残す（ID入力前に選んだ言語は「はじめる」時に記録）
  if (log && participantId.value) {
    postJson('/api/event', { event: 'ui_language', detail: code }).catch(() => {})
  }
}

// チャットの文言：アシスタントの定型文はキーで持ち、言語を切り替えると表示も変わる
function messageText(message) {
  return message.key ? t(message.key, message.params) : message.content
}

// API のエラー：コードがあれば今の言語で、無ければサーバーの文言をそのまま
function errorText(error) {
  return error.code ? t(`err.${error.code}`) : error.message
}

const participantId = ref('')
const idInput = ref('')
const starting = ref(false)
const startError = ref(null) // { prefix: 文言キー, error }。言語を切り替えても訳し直せるよう、文字列にせず持つ
const startErrorText = computed(() =>
  startError.value ? t(startError.value.prefix) + errorText(startError.value.error) : ''
)
const systemStatus = ref('checking') // checking | ok | backend_down | comfy_down
let healthTimer = null

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`)
    const data = await response.json()
    systemStatus.value = data.comfyui ? 'ok' : 'comfy_down'
  } catch (error) {
    systemStatus.value = 'backend_down'
  }
}

onMounted(() => {
  checkHealth()
  healthTimer = setInterval(checkHealth, 5000)
})

const systemStatusText = computed(() => {
  return t(`status.${systemStatus.value}`)
})

const inputText = ref('')
const loading = ref(false)
const currentImage = ref('')
const displayVersion = ref(0)
const latestVersion = ref(0)
const finalVersion = ref(0)
const chatBody = ref(null)
const stripEl = ref(null)
const composerInput = ref(null)

// 入力欄にカーソルを戻す（生成のたびにクリックし直さなくて済むように）
async function focusInput() {
  await nextTick()
  if (composerInput.value && !composerInput.value.disabled) composerInput.value.focus()
}

// 次の修正のもとになるバージョン（ふつうは最新。「この Ver. から修正する」で古い版にも戻せる）
const baseVersion = ref(0)

// 比べる画面：左右それぞれ imageHistory の何番目を表示するか
const compare = ref(null)
function openCompare() {
  const count = imageHistory.value.length
  if (count < 2) return
  const shown = Math.max(imageHistory.value.findIndex((item) => item.version === displayVersion.value), 0)
  // 右に今見ている版、左にそのひとつ前（先頭を見ているときは次の版を右に）
  compare.value = shown > 0 ? { left: shown - 1, right: shown } : { left: 0, right: 1 }
}
const imageHistory = ref([])
const showImageModal = ref(false)

// ページ内の確認ダイアログ（ブラウザ標準の confirm/alert は埋め込みブラウザ等で表示されないことがあるため使わない）
const dialog = ref(null)
let dialogResolve = null

function askDialog({ message, okText = 'OK', cancelText = null, danger = false }) {
  if (dialogResolve) dialogResolve(false)
  dialog.value = { message, okText, cancelText, danger }
  return new Promise((resolve) => {
    dialogResolve = resolve
  })
}

function closeDialog(result) {
  dialog.value = null
  if (dialogResolve) {
    const resolve = dialogResolve
    dialogResolve = null
    resolve(result)
  }
}

const messages = ref([])

// 生成中のひとこと（少しずつ切り替えて待ち時間を和らげる）
const loadingIndex = ref(0)
let loadingTimer = null
const loadingText = computed(() => {
  const texts = t('loading')
  return texts[loadingIndex.value % texts.length]
})

watch(loading, (value) => {
  clearInterval(loadingTimer)
  loadingIndex.value = 0
  if (value) {
    loadingTimer = setInterval(() => {
      loadingIndex.value += 1
    }, 2500)
  }
})

// 倒计时（到时只提醒，不强制中断）
const remainingSeconds = ref(TIME_LIMIT_SECONDS)
const timeNotice = ref('')
let timerId = null
let sessionStartedAt = 0
let warned = false
let timeUp = false

const RING_LENGTH = 2 * Math.PI * 19
const ringOffset = computed(() => {
  const ratio = Math.min(Math.max(remainingSeconds.value / TIME_LIMIT_SECONDS, 0), 1)
  return RING_LENGTH * (1 - ratio)
})

// 「最初から作り直す」を選んだ状態（次のメッセージは修正ではなく新規生成になる）
const restartPending = ref(false)

const timeText = computed(() => {
  const s = Math.max(remainingSeconds.value, 0)
  const m = String(Math.floor(s / 60)).padStart(2, '0')
  const r = String(s % 60).padStart(2, '0')
  return `${m}:${r}`
})

function postJson(path, body) {
  // 每次请求都带上当前参加者ID：后端重启或被重置后，可以据此自动恢复会话
  const payload = { ...(participantId.value ? { participant_id: participantId.value } : {}), ...(body || {}) }
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

function apiError(code, message) {
  const error = new Error(message || code)
  error.code = code
  return error
}

// POST して JSON を返す。失敗時は error.code（翻訳用）付きの Error を投げる（技術的な内容は出さない）
async function callApi(path, body) {
  let response
  try {
    response = await postJson(path, body)
  } catch (error) {
    throw apiError('OFFLINE')
  }
  let data = {}
  try {
    data = await response.json()
  } catch (error) {
    data = {}
  }
  if (!response.ok) throw apiError(data.code || (data.error ? '' : 'UNKNOWN'), data.error)
  return data
}

// ページを再読み込みしても続きから再開できるよう、進行中の参加者IDをブラウザに覚えておく
const SESSION_KEY = 'avatar_maker_participant'
function rememberSession(id) {
  try {
    if (id) localStorage.setItem(SESSION_KEY, id)
    else localStorage.removeItem(SESSION_KEY)
  } catch (error) {
    /* 保存できない環境では再開機能なしで動く */
  }
}
function savedSession() {
  try {
    return localStorage.getItem(SESSION_KEY) || ''
  } catch (error) {
    return ''
  }
}

function stopTimer() {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

// elapsedSeconds：再開時にすでに経過している秒数（警告・時間切れは記録済みなので再送しない）
function startTimer(elapsedSeconds = 0) {
  stopTimer()
  sessionStartedAt = Date.now() - elapsedSeconds * 1000
  remainingSeconds.value = TIME_LIMIT_SECONDS - elapsedSeconds
  timeNotice.value = ''
  warned = remainingSeconds.value <= WARNING_SECONDS
  timeUp = remainingSeconds.value <= 0
  if (timeUp) timeNotice.value = 'timeUp'
  else if (warned) timeNotice.value = 'warn2'

  timerId = setInterval(() => {
    const elapsed = Math.floor((Date.now() - sessionStartedAt) / 1000)
    remainingSeconds.value = TIME_LIMIT_SECONDS - elapsed

    if (!warned && remainingSeconds.value <= WARNING_SECONDS && remainingSeconds.value > 0) {
      warned = true
      timeNotice.value = 'warn2'
      postJson('/api/event', { event: 'time_warning' }).catch(() => {})
    }

    if (!timeUp && remainingSeconds.value <= 0) {
      timeUp = true
      timeNotice.value = 'timeUp'
      postJson('/api/event', { event: 'time_up' }).catch(() => {})
    }
  }, 1000)
}

onBeforeUnmount(() => {
  stopTimer()
  clearInterval(loadingTimer)
  if (healthTimer) clearInterval(healthTimer)
})

function resetLocalState() {
  messages.value = [
    { id: Date.now(), role: 'assistant', key: 'welcome' }
  ]
  currentImage.value = ''
  displayVersion.value = 0
  latestVersion.value = 0
  baseVersion.value = 0
  compare.value = null
  finalVersion.value = 0
  imageHistory.value = []
  restartPending.value = false
  inputText.value = ''
  showImageModal.value = false
  closeDialog(false)
  timeNotice.value = ''
}

// 開始画面の段階：ID 入力 → 質問1
const startStep = ref('id')
const q1Answer = ref(0)
const p2Answer = ref(0) // 質問2：今のイメージの決まり具合
function toQ1() {
  if (!idInput.value.trim()) return
  startError.value = null
  startStep.value = 'q1'
}

async function startSession() {
  const id = idInput.value.trim()
  if (!id || starting.value || !q1Answer.value || !p2Answer.value) return

  starting.value = true
  startError.value = null

  try {
    const data = await callApi('/api/start', { participant_id: id })
    resetLocalState()
    participantId.value = data.participant_id // 全角で入力しても半角に直ったIDが返る
    rememberSession(data.participant_id)
    postJson('/api/event', { event: 'ui_language', detail: lang.value }).catch(() => {})
    postJson('/api/event', { event: 'pre_experience', detail: String(q1Answer.value) }).catch(() => {})
    postJson('/api/event', { event: 'pre_clarity', detail: String(p2Answer.value) }).catch(() => {})
    startStep.value = 'id'
    q1Answer.value = 0
    p2Answer.value = 0
    startTimer()
    focusInput()
  } catch (error) {
    startError.value = { prefix: '', error }
    startStep.value = 'id' // ID の誤りなどは ID 入力に戻して直してもらう
  } finally {
    starting.value = false
  }
}

// 再読み込み後：同じブラウザで進行中だった回があれば、履歴・最終選択・残り時間を復元する
async function resumeSession() {
  const id = savedSession()
  if (!id) return

  starting.value = true
  try {
    const data = await callApi('/api/resume', { participant_id: id })
    if (!data.active) {
      rememberSession('')
      return
    }

    resetLocalState()
    for (const [index, item] of data.items.entries()) {
      const image = `${API_BASE}${item.image}`
      if (index > 0 && item.action === 'generate') {
        messages.value.push({ id: `r${item.version}`, role: 'assistant', key: 'restartMsg' })
      }
      messages.value.push(
        { id: `u${item.version}`, role: 'user', content: item.prompt },
        {
          id: `a${item.version}`,
          role: 'assistant',
          key: item.action === 'edit' ? 'edited' : 'generated',
          params: { v: item.version }
        }
      )
      imageHistory.value.push({
        id: `h${item.version}`,
        version: item.version,
        image,
        message: item.prompt,
        action: item.action
      })
    }
    messages.value.push({ id: 'resumed', role: 'assistant', key: 'resumed' })
    if (data.pending_restart && data.items.length) {
      restartPending.value = true
      messages.value.push({ id: 'restart-pending', role: 'assistant', key: 'restartMsg' })
    }

    const last = imageHistory.value[imageHistory.value.length - 1]
    if (last) {
      latestVersion.value = last.version
      displayVersion.value = last.version
      currentImage.value = last.image
    }
    if (last && !data.pending_restart) {
      baseVersion.value = data.base_version || last.version
      if (baseVersion.value !== last.version) {
        messages.value.push({
          id: 'base',
          role: 'assistant',
          key: 'baseChanged',
          params: { v: baseVersion.value }
        })
      }
    }
    finalVersion.value = data.final_version || 0
    participantId.value = data.participant_id
    startTimer(data.elapsed_sec)
    scrollToBottom()
    focusInput()
  } catch (error) {
    startError.value = { prefix: 'resumeFailed', error }
  } finally {
    starting.value = false
  }
}

onMounted(resumeSession)

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
    const data = await callApi('/api/generate', { message: text })

    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      key: data.action === 'edit' ? 'edited' : 'generated',
      params: { v: data.version }
    })

    latestVersion.value = data.version
    baseVersion.value = data.version
    displayVersion.value = data.version
    currentImage.value = data.image

    imageHistory.value.push({
      id: Date.now() + 2,
      version: data.version,
      image: data.image,
      message: text,
      action: data.action
    })
    restartPending.value = false
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      key: error.code ? `err.${error.code}` : '',
      content: error.message
    })
  } finally {
    loading.value = false
    scrollToBottom()
    focusInput()
  }
}

async function restartDesign() {
  if (loading.value) return
  const ok = await askDialog({
    message: t('restartConfirm'),
    okText: t('restartOk'),
    cancelText: t('back')
  })
  if (!ok) return

  try {
    await callApi('/api/restart')
    restartPending.value = true
    messages.value.push({ id: Date.now(), role: 'assistant', key: 'restartMsg' })
    scrollToBottom()
    focusInput()
  } catch (error) {
    await askDialog({ message: errorText(error) })
  }
}

async function cancelRestart() {
  try {
    const data = await callApi('/api/restart', { cancel: true })
    restartPending.value = false
    baseVersion.value = data.base_version || latestVersion.value
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      key: 'restartCancelled',
      params: { v: baseVersion.value }
    })
    scrollToBottom()
    focusInput()
  } catch (error) {
    await askDialog({ message: errorText(error) })
  }
}

// 今見ている（古い）バージョンを、次の修正のもとにする
async function setBase() {
  const version = displayVersion.value
  if (!version || loading.value) return
  try {
    await callApi('/api/base', { version })
    baseVersion.value = version
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      key: 'baseChanged',
      params: { v: version }
    })
    scrollToBottom()
    focusInput()
  } catch (error) {
    await askDialog({ message: errorText(error) })
  }
}

function viewHistory(item) {
  currentImage.value = item.image
  displayVersion.value = item.version
}

async function chooseFinal() {
  if (!displayVersion.value || loading.value) return

  try {
    await callApi('/api/final', { version: displayVersion.value })
    finalVersion.value = displayVersion.value
  } catch (error) {
    await askDialog({ message: t('recordFailed') + errorText(error) })
  }
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
  link.download = `${participantId.value}_v${displayVersion.value || 'current'}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// ===== 終了後のお礼とオンライン用アンケート =====
const thanks = ref(null) // { pid, final }：終了した参加者（画面の状態はもう消えているので、ここで持つ）
const surveyOpen = ref(false)
const surveyState = ref('idle') // idle | sending | sent | error
const surveyError = ref('')
function newSurvey() {
  return { q1: 0, q2: 0, qc: 0, q3: 0, q4: [], q4_other: '', q5: [], q5_other: '', q6: [], q6_other: '', q7: '' }
}
const survey = ref(newSurvey())
const S = computed(() => SURVEY[lang.value] || SURVEY.ja)
// 1〜3 は選んだか、4〜6 は1つ以上選んだか（7 は任意）
// 画面に出す番号（紙と同じ）。質問1・2は開始時に画面で回答済み
const NUM = { qc: 3, q3: 4, q4: 5, q5: 6, q6: 7, q7: 8 }
const REQUIRED = ['qc', 'q3', 'q4', 'q5', 'q6']
function answered(q) {
  const value = survey.value[q]
  return Array.isArray(value) ? value.length > 0 : Boolean(value)
}
const surveyReady = computed(() => REQUIRED.every(answered))

const showMissing = ref(false) // 送信を押したのに 1〜3 が未回答のときだけ true

async function submitSurvey() {
  if (!thanks.value) return
  if (!surveyReady.value) {
    showMissing.value = true
    await nextTick()
    const first = REQUIRED.find((q) => !answered(q))
    document.querySelector(`.survey [data-q="${first}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }
  surveyState.value = 'sending'
  try {
    await callApi('/api/survey', {
      participant_id: thanks.value.pid,
      final_version: thanks.value.final || 0,
      lang: lang.value,
      answers: survey.value
    })
    surveyState.value = 'sent'
  } catch (error) {
    surveyError.value = S.value.failed + errorText(error)
    surveyState.value = 'error'
  }
}

// お礼を閉じたら、次の人のために日本語の画面に戻す
function closeThanks() {
  thanks.value = null
  surveyOpen.value = false
  showMissing.value = false
  survey.value = newSurvey()
  surveyState.value = 'idle'
  surveyError.value = ''
  setLang('ja', { log: false })
}

async function finishSession() {
  const noFinal = imageHistory.value.length > 0 && !finalVersion.value
  const chosen = finalVersion.value
  const pid = participantId.value
  const ok = await askDialog({
    message: noFinal
      ? t('finishNoFinal')
      : chosen
        ? t('finishConfirm', { v: chosen })
        : t('finishConfirmEmpty'),
    okText: t('finishOk'),
    cancelText: t('back'),
    danger: true
  })
  if (!ok) return

  try {
    await postJson('/api/event', { event: 'finish' }).catch(() => {})
    await callApi('/api/reset')
  } catch (error) {
    console.error(error)
    await askDialog({ message: t('finishFailed') + errorText(error) })
    return
  }

  rememberSession('')
  stopTimer()
  resetLocalState()
  participantId.value = ''
  idInput.value = ''
  // お礼（参加者が使っていた言語で）。閉じると closeThanks() で日本語に戻る
  thanks.value = { pid, final: chosen }
}

// 履歴が増えたら、いちばん新しいサムネイルが見える位置まで送る
watch(
  () => imageHistory.value.length,
  async () => {
    await nextTick()
    if (stripEl.value) stripEl.value.scrollTo({ left: stripEl.value.scrollWidth, behavior: 'smooth' })
    // スマホなど縦に並ぶ画面では、画像が入力欄より上にあるので、新しい画像が見える位置まで戻す
    if (window.innerWidth < 760) {
      document.querySelector('.frame')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
)

async function scrollToBottom() {
  await nextTick()

  if (chatBody.value) {
    chatBody.value.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' })
  }
}
</script>

<style scoped>
.app {
  --ink: #1f1e1d;
  --muted: #6f6c64;
  --faint: #a3a097;
  --line: #e8e6dc;
  --soft: #f4f2ec;
  --panel: #ffffff;
  --primary: #d97757;        /* 強調色：テラコッタ系のオレンジ */
  --primary-hover: #c6613f;
  --primary-soft: rgba(217, 119, 87, 0.16);
  --accent: #d97757;
  --user-bubble: #f0eee6;
  --ok: #3f8f5b;
  --warn: #c2410c;
  --danger: #c0392b;
  --serif: 'Hiragino Mincho ProN', 'Yu Mincho', 'Noto Serif JP', Georgia, serif;

  /* レイアウトの基準：画像エリアの高さ → 2:3 の画像の幅 → 全体の幅 */
  --stage-h: clamp(520px, calc(100dvh - 104px), 1300px);
  --under-h: 104px;
  --gap: 24px;
  --chat-w: clamp(360px, 32vw, 520px);
  --stage-w: min(
    calc((var(--stage-h) - var(--under-h) - 14px) * 2 / 3),
    calc(100vw - var(--chat-w) - var(--gap) - 2 * clamp(16px, 3vw, 40px))
  );
  --shell-w: calc(var(--stage-w) + var(--gap) + var(--chat-w));

  min-height: 100dvh;
  box-sizing: border-box;
  padding: 0 clamp(16px, 3vw, 40px) 28px;
  color: var(--ink);
  font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic UI', 'Noto Sans JP',
    system-ui, -apple-system, 'Segoe UI', sans-serif;
  background: #faf9f5;
  overflow-x: hidden;
}

.app * {
  box-sizing: border-box;
}

/* ===== 開始画面 ===== */
.start {
  position: relative;
  min-height: calc(100dvh - 28px); /* 減去 .app 底部留白，避免开始页出现多余滚动条 */
  display: grid;
  place-items: center;
  padding: 72px 0 24px;
  /* 説明ページと同じパステルの背景（人物は描いていない）。左右と下は白へ溶かす */
  margin: 0 calc(-1 * clamp(16px, 3vw, 40px)) -28px;
  background:
    linear-gradient(to bottom, rgba(250, 249, 245, 0) 55%, #faf9f5 100%),
    url('/start-bg.jpg') center top / cover no-repeat;
}

.start-card {
  width: min(560px, calc(100% - 32px));
  padding: 40px clamp(20px, 5vw, 48px) 32px;
  text-align: center;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  box-shadow: 0 18px 48px rgba(120, 80, 110, 0.12);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}

.logo-orb {
  width: 56px;
  height: 56px;
  margin: 0 auto 22px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--primary);
}

.logo-orb svg {
  width: 28px;
  height: 28px;
}

.start-title {
  margin: 0;
  font-size: clamp(24px, 5.6vw, 34px);
  line-height: 1.4;
  white-space: pre-line;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #2a2346;
}

.start-lead {
  margin: 14px 0 0;
  font-size: 15px;
  line-height: 1.7;
  color: #4a4560;
}

.start-chips {
  margin: 18px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.start-chips li {
  padding: 5px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary-hover);
  background: #fff;
  border: 1px solid #f0d9cf;
  border-radius: 999px;
}

.start-rules {
  margin: 14px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.start-sub {
  margin: 26px 0 14px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 15px;
}

.start-form {
  display: flex;
  gap: 10px;
  max-width: 300px; /* ID は短い数字なので、入力欄はタイトルより短くしてまとまりよく見せる */
  margin: 0 auto;
}

.start-form input {
  flex: 1;
  min-width: 0;
  height: 52px;
  padding: 0 16px;
  font: inherit;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-align: center;
  color: var(--ink);
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 12px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.start-form input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--primary-soft);
}

.go {
  height: 52px;
  padding: 0 26px;
  font: inherit;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: var(--primary);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.go:hover:not(:disabled) {
  background: var(--primary-hover);
}

.go:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.sys {
  margin: 20px 0 0;
  font-size: 13px;
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.sys .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--faint);
}

.start-q1 {
  margin-top: 26px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
}

.start-q1-note {
  margin: 0 0 6px;
  font-size: 13px;
  color: var(--muted);
}

.start-q1-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.6;
}

.start-q1-opts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.start-q1-opts button {
  padding: 8px 14px;
  font: inherit;
  font-size: 14px;
  color: var(--ink);
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 999px;
  cursor: pointer;
}

.start-q1-opts button:hover {
  border-color: var(--primary);
}

.start-q1-opts button.on {
  color: #fff;
  background: var(--primary);
  border-color: var(--primary);
}

.start-q2-title {
  margin-top: 22px;
}

.start-scale button b {
  margin-right: 6px;
}

.start-q1-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.start-back {
  height: 52px;
  padding: 0 20px;
  font: inherit;
  font-weight: 700;
  color: var(--muted);
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 12px;
  cursor: pointer;
}

.start-error {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--danger);
}

.sys.ok { color: var(--ok); }
.sys.ok .dot { background: var(--ok); }
.sys.comfy_down,
.sys.backend_down { color: var(--danger); }
.sys.comfy_down .dot,
.sys.backend_down .dot { background: var(--danger); }

/* ===== ヘッダー ===== */
.top {
  max-width: var(--shell-w);
  height: 64px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--primary);
}

.brand-mark svg {
  width: 16px;
  height: 16px;
}

.brand-name {
  font-family: var(--serif);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 18px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
}

.id-pill {
  color: var(--ink);
}

/* 言語切り替え（3つのボタンの下を白いつまみが滑る） */
.lang {
  --n: 3;
  position: relative;
  display: grid;
  grid-template-columns: repeat(var(--n), 1fr);
  padding: 3px;
  border-radius: 999px;
  background: var(--soft);
  border: 1px solid var(--line);
}

.lang-thumb {
  position: absolute;
  top: 3px;
  bottom: 3px;
  left: 3px;
  width: calc((100% - 6px) / var(--n));
  border-radius: 999px;
  background: var(--panel);
  box-shadow: 0 1px 3px rgba(31, 30, 29, 0.14);
  transform: translateX(calc(var(--i) * 100%));
  transition: transform 0.25s ease;
}

.lang button {
  position: relative;
  z-index: 1;
  padding: 6px 12px;
  border: none;
  background: none;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.2s;
}

.lang button.on {
  color: var(--primary);
}

.start-lang {
  position: absolute;
  top: 20px;
  right: clamp(16px, 3vw, 40px);
  z-index: 2;
}

.timer {
  position: relative;
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
}

.ring {
  position: absolute;
  inset: 0;
  width: 52px;
  height: 52px;
  transform: rotate(-90deg);
}

.ring circle {
  fill: none;
  stroke-width: 3;
}

.ring-bg { stroke: var(--line); }

.ring-fg {
  stroke: var(--primary);
  stroke-linecap: round;
  stroke-dasharray: 119.38;
  transition: stroke-dashoffset 1s linear, stroke 0.3s;
}

.timer.warn .ring-fg { stroke: var(--warn); }
.timer.warn .timer-text { color: var(--warn); }

.timer-text {
  position: relative;
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

/* ===== 時間のお知らせ ===== */
.toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  max-width: min(560px, calc(100vw - 32px));
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 18px;
  font-weight: 600;
  color: #9a3412;
  background: #fff7ed;
  border: 1px solid #f5c6a5;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
}

.toast button {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}

.toast-enter-active,
.toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from,
.toast-leave-to { opacity: 0; transform: translate(-50%, -12px); }

/* ===== メイン ===== */
/* 画像（左）とチャット（右）を、画像の大きさに合わせた幅でまとめて中央に置く */
.main {
  max-width: var(--shell-w);
  margin: 0 auto;
  display: grid;
  grid-template-columns: var(--stage-w) minmax(0, 1fr);
  gap: var(--gap);
  align-items: stretch;
}

/* ----- ステージ ----- */
.stage {
  container: stage / inline-size;
  height: var(--stage-h);
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  min-width: 0;
}

/* 画像を置ける最大の領域。ここを基準にフレームの大きさを決める */
.frame-wrap {
  flex: 1 1 0;
  min-height: 0;
  container-type: size;
  display: grid;
  place-items: center;
}

/* 画像の下：履歴（左）と最終画像ボタン（右） */
.under {
  flex: none;
  height: var(--under-h); /* 高さ固定：履歴や最終画像の表示が増えても画像の大きさは変わらない */
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.frame {
  position: relative;
  /* 生成画像と同じ 2:3（1024×1536）。領域に収まる最大サイズで、比率は常に固定 */
  height: min(100cqh, calc(100cqw * 3 / 2));
  aspect-ratio: 2 / 3;
  border-radius: 20px;
  background: var(--panel);
  border: 1px solid var(--line);
  box-shadow: 0 1px 2px rgba(31, 30, 29, 0.04), 0 12px 32px -18px rgba(31, 30, 29, 0.18);
  overflow: hidden;
  display: grid;
  place-items: center;
}

.frame.busy {
  background: var(--soft);
}

.art {
  width: 100%;
  height: 100%;
  object-fit: contain;
  cursor: zoom-in;
  display: block;
}

.empty {
  display: grid;
  justify-items: center;
  gap: 14px;
  color: var(--faint);
  font-size: 14px;
}

.empty p {
  margin: 0;
}

.empty-orb {
  color: #dcd9ce;
}

.empty-orb svg {
  width: 56px;
  height: 56px;
}

/* 読み込み */
.loading {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}

.shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255, 255, 255, 0.7) 50%, transparent 70%);
  background-size: 220% 100%;
  animation: shimmer 1.8s linear infinite;
}

@keyframes shimmer {
  from { background-position: 120% 0; }
  to { background-position: -120% 0; }
}

.loading-center {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 16px;
}

.loading-text {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
}

.orbit {
  width: 36px;
  height: 36px;
  border: 3px solid var(--line);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.orbit i {
  display: none;
}

@keyframes spin { to { transform: rotate(360deg); } }

.ver-badge {
  position: absolute;
  left: 12px;
  top: 12px;
  padding: 6px 12px;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  border-radius: 999px;
}

.ver-badge b {
  color: var(--warn);
}

.zoom {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  border-radius: 10px;
  cursor: pointer;
}

.zoom:hover { background: #fff; }

.pop-enter-active { transition: opacity 0.35s ease; }
.pop-leave-active { transition: opacity 0.15s ease; }
.pop-enter-from,
.pop-leave-to { opacity: 0; }

.edit-note {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px 12px;
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--line);
  border-radius: 14px;
}

.edit-note button {
  padding: 7px 14px;
  font: inherit;
  font-weight: 700;
  color: #fff;
  background: var(--primary);
  border: none;
  border-radius: 999px;
  cursor: pointer;
}

.edit-note button:hover {
  background: var(--primary-hover);
}

/* 「比べる」：拡大ボタンの左 */
.compare-btn {
  position: absolute;
  right: 56px;
  top: 12px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  border-radius: 10px;
  cursor: pointer;
}

.compare-btn:hover { background: #fff; }

/* 履歴 */
.strip {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding: 6px 4px 2px;
  scrollbar-width: thin;
}

.thumb {
  position: relative;
  flex: none;
  width: 42px;
  padding: 0;
  font: inherit;
  background: none;
  border: none;
  cursor: pointer;
  text-align: center;
}

.thumb img {
  width: 42px;
  height: 56px;
  object-fit: cover;
  display: block;
  border-radius: 8px;
  border: 2px solid transparent;
  outline: 1px solid var(--line);
  transition: border-color 0.15s;
}

.thumb:hover img {
  border-color: #dcd9ce;
}

.thumb span {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--faint);
}

/* まだ画像が無いとき：ここに履歴が並ぶことを示す空き枠 */
.thumb.ghost {
  cursor: default;
}

.thumb.ghost i {
  display: block;
  width: 42px;
  height: 56px;
  box-sizing: border-box;
  border: 1.5px dashed #dcd9ce;
  border-radius: 8px;
}

.thumb.active img {
  border-color: var(--accent);
}

.thumb.active span { color: var(--accent); }

.thumb .star {
  position: absolute;
  right: -4px;
  top: -6px;
  font-style: normal;
  font-size: 14px;
  color: var(--warn);
}

/* 最終画像ボタン */
.final-row {
  flex: 0 1 300px;
  min-width: 150px;
  padding-top: 6px;
  text-align: center;
}

.final {
  width: 100%;
  min-height: 46px;
  padding: 4px 10px;
  line-height: 1.3;
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  background: var(--primary);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: opacity 0.15s, background 0.2s;
}

.final:hover:not(.chosen):not(:disabled) { background: var(--primary-hover); }

.final:disabled {
  color: var(--faint);
  background: var(--soft);
  border: 1px solid var(--line);
  cursor: default;
}

.final.chosen {
  background: var(--ok);
}

.final-hint.hidden {
  visibility: hidden;
}

/* 画像エリアが狭いとき：ボタンの文字を小さくして1行に収める */
@container stage (max-width: 460px) {
  .final-row {
    flex-basis: 190px;
  }

  .final {
    font-size: 13px;
  }

  .final-hint {
    font-size: 11.5px;
  }
}

.final-hint {
  margin: 6px 0 0;
  line-height: 1.35;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ok);
}

/* ----- チャット ----- */
.chat {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: var(--stage-h);
  box-sizing: border-box;
  padding: 20px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(31, 30, 29, 0.04), 0 12px 32px -18px rgba(31, 30, 29, 0.18);
}

.chat-body {
  scrollbar-width: thin;
  scrollbar-color: #dcd9ce transparent;
}

.chat-body::-webkit-scrollbar {
  width: 6px;
}

.chat-body::-webkit-scrollbar-thumb {
  background: #dcd9ce;
  border-radius: 999px;
}

.chat-body::-webkit-scrollbar-button {
  display: none;
}

/* 会話は下（入力欄のそば）から積み上げる */
.chat-body > :first-child {
  margin-top: auto;
}

.chat-body {
  flex: 1 1 0;
  height: 0; /* 内容多了也不撑高，只在内部滚动 */
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.msg {
  max-width: 88%;
  padding: 11px 15px;
  font-size: 15px;
  line-height: 1.65;
  border-radius: 16px;
}

.msg p {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.msg.assistant {
  align-self: flex-start;
  background: #fff;
  border: 1px solid var(--line);
  border-bottom-left-radius: 4px;
}

.msg.user {
  align-self: flex-end;
  color: var(--ink);
  background: var(--user-bubble);
  border-bottom-right-radius: 4px;
}

.typing { padding: 13px 16px; }

.dots {
  display: inline-flex;
  gap: 5px;
}

.dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--faint);
  animation: bounce 1s ease-in-out infinite;
}

.dots i:nth-child(2) { animation-delay: 0.15s; }
.dots i:nth-child(3) { animation-delay: 0.3s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.composer {
  position: relative;
}

/* 「最初から作り直す」：入力欄のすぐ上に控えめに置く */
.restart-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: -4px;
}

.restart-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: -4px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary-hover);
  background: var(--primary-soft);
  border-radius: 10px;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 6px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
}

.link-btn:hover {
  color: var(--primary-hover);
  background: var(--soft);
}

.restart-bar .link-btn {
  color: var(--primary-hover);
  text-decoration: underline;
}

.composer textarea {
  width: 100%;
  min-height: 76px;
  max-height: 150px;
  padding: 13px 60px 13px 14px;
  font: inherit;
  font-size: 15px;
  line-height: 1.5;
  color: var(--ink);
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 14px;
  outline: none;
  resize: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.composer textarea::placeholder {
  color: var(--faint);
}

.composer textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--primary-soft);
}

.composer textarea:disabled {
  background: #fafafa;
}

.send {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--primary);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.send svg {
  width: 18px;
  height: 18px;
}

.send:hover:not(:disabled) { background: var(--primary-hover); }
.send:disabled { opacity: 0.25; cursor: not-allowed; }

.finish {
  align-self: center;
  padding: 8px 16px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  border: 1px solid var(--line);
  border-radius: 999px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.finish:hover {
  color: var(--danger);
  border-color: #e7a99d;
}

/* ===== モーダル（拡大・確認） ===== */
.modal {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(31, 30, 29, 0.45);
}

.modal-box {
  position: relative;
  max-width: min(92vw, 720px);
  max-height: 94vh;
  display: grid;
  gap: 14px;
  justify-items: center;
}

.modal-box img {
  max-width: 100%;
  max-height: 80vh;
  border-radius: 14px;
  background: #fff;
}

/* 比べる画面 */
.compare-box {
  position: relative;
  display: flex;
  gap: 16px;
  max-width: 96vw;
}

.compare-pane {
  display: grid;
  gap: 10px;
  justify-items: center;
  min-width: 0;
}

.compare-pane img {
  display: block;
  max-width: 100%;
  max-height: calc(100dvh - 130px);
  aspect-ratio: 2 / 3;
  object-fit: contain;
  border-radius: 14px;
  background: #fff;
}

.compare-nav {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  background: #fff;
  border-radius: 999px;
}

.compare-nav span {
  min-width: 76px;
  text-align: center;
}

.compare-nav b {
  color: var(--warn);
}

.compare-nav button {
  width: 36px;
  height: 36px;
  font: inherit;
  font-size: 22px;
  line-height: 1;
  color: var(--ink);
  background: var(--soft);
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.compare-nav button:disabled {
  opacity: 0.3;
  cursor: default;
}

.modal-close {
  position: absolute;
  right: -10px;
  top: -14px;
  width: 36px;
  height: 36px;
  font-size: 20px;
  color: var(--ink);
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 50%;
  cursor: pointer;
}

.save {
  height: 44px;
  padding: 0 22px;
  font: inherit;
  font-weight: 700;
  color: var(--ink);
  background: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.dialog-box {
  width: min(420px, 100%);
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(17, 24, 39, 0.2);
}

/* 終了後のお礼＋オンライン用アンケート */
.thanks-box {
  width: min(720px, 100%);
  max-height: 92vh;
  overflow-y: auto;
  padding: 26px 26px 22px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(17, 24, 39, 0.2);
}

.thanks-box .dialog-message {
  margin-bottom: 8px;
}

.thanks-onsite {
  margin: 0 0 18px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--muted);
}

.survey {
  margin: 0 0 18px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
}

.survey summary {
  padding: 14px 18px;
  border-radius: 14px;
  background: #fdf3ee;
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-hover);
  cursor: pointer;
}

.survey[open] summary {
  border-bottom: 1px solid #f3e0d7;
  border-radius: 14px 14px 0 0;
}

.survey-note {
  margin: 14px 18px 0;
  font-size: 13px;
  color: var(--muted);
}

.survey-form {
  padding: 0 18px 18px;
}

.survey-final {
  margin: 14px 0 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--muted);
}

.survey-final b {
  padding: 3px 10px;
  font-size: 15px;
  color: var(--ink);
  background: var(--soft);
  border-radius: 8px;
}

/* 1問ずつ、細い線で区切る */
.survey .q {
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
}

.survey .q:last-of-type {
  border-bottom: none;
}

.survey h4 {
  position: relative;
  margin: 0 0 12px;
  padding-left: 34px; /* 番号の丸は左に固定し、題が長くても丸だけ1行にならないように */
  font-size: 15px;
  line-height: 1.6;
  font-weight: 700;
}

.survey .q-no {
  position: absolute;
  left: 0;
  top: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 13px;
  color: #fff;
  background: var(--primary);
}

.survey h4 small,
.survey h4 .req,
.survey h4 .count {
  display: inline-block;
  margin-left: 8px;
  vertical-align: 1px;
}

.survey h4 small {
  font-size: 12px;
  font-weight: 400;
  color: var(--faint);
}

.survey h4 .req {
  padding: 1px 7px;
  font-size: 11px;
  font-style: normal;
  font-weight: 700;
  color: var(--primary-hover);
  background: #fdf3ee;
  border-radius: 6px;
}

.survey .q.missing h4 {
  color: var(--danger);
}

.survey .q.missing .scale-opt,
.survey .q.missing .chip {
  border-color: #e8a59b;
}

.survey h4 .count {
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
  color: var(--muted);
}

/* 見た目だけ隠す（キーボード・読み上げでは使える） */
.survey .vh {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

/* 5段階：横一列 */
.survey .scale {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.survey .scale-opt {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 64px;
  padding: 8px 6px;
  text-align: center;
  font-size: 12.5px;
  line-height: 1.4;
  color: var(--ink);
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.survey .scale-opt b {
  font-size: 16px;
}

.survey .scale-opt span {
  white-space: pre-line;
}

.survey .scale-opt:hover,
.survey .chip:hover {
  border-color: var(--primary);
}

.survey .scale-opt.on,
.survey .chip.on {
  color: #fff;
  background: var(--primary);
  border-color: var(--primary);
}

.survey .scale-opt:focus-within,
.survey .chip:focus-within {
  box-shadow: 0 0 0 3px var(--primary-soft);
}

/* 複数選択：タグを横に並べる */
.survey .chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.survey .chip {
  position: relative;
  padding: 7px 14px;
  font-size: 13.5px;
  line-height: 1.4;
  color: var(--ink);
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s, opacity 0.15s;
}

.survey .chip.off {
  opacity: 0.4;
  cursor: not-allowed;
}

.survey .chip-group + .chip-group {
  margin-top: 12px;
}

.survey .group-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.survey .other-input,
.survey textarea {
  width: 100%;
  margin-top: 10px;
  padding: 9px 12px;
  font: inherit;
  font-size: 14px;
  background: #fff;
  border: 1px solid #dcd9ce;
  border-radius: 10px;
  outline: none;
  resize: vertical;
}

.survey .other-input:focus,
.survey textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-soft);
}

.survey textarea {
  margin-top: 0;
}

/* 狭い画面では5段階を縦に */
@media (max-width: 560px) {
  .survey .scale {
    grid-template-columns: 1fr;
  }
  .survey .scale-opt {
    flex-direction: row;
    justify-content: flex-start;
    min-height: 0;
    gap: 10px;
    text-align: left;
  }
}

.survey-submit {
  margin-top: 16px;
  height: 42px;
  padding: 0 22px;
  font: inherit;
  font-weight: 700;
  border-radius: 10px;
  cursor: pointer;
}

.survey-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.survey-hint,
.survey-error {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.survey-error {
  color: var(--danger);
}

.survey-sent {
  margin: 14px 16px 16px;
  font-size: 14px;
  font-weight: 700;
  color: var(--ok);
}

.dialog-message {
  white-space: pre-line;
  margin: 0 0 22px;
  font-size: 16px;
  line-height: 1.7;
  color: var(--ink);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dialog-actions button {
  height: 42px;
  padding: 0 18px;
  font: inherit;
  font-weight: 700;
  border-radius: 10px;
  cursor: pointer;
}

.dialog-cancel {
  color: var(--ink);
  background: #fff;
  border: 1px solid #dcd9ce;
}

.dialog-ok {
  color: #fff;
  background: var(--primary);
  border: none;
}

.dialog-ok.danger {
  background: var(--danger);
}

.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

/* ===== レスポンシブ ===== */
@media (max-width: 980px) {
  .app {
    --shell-w: 640px;
  }

  .main {
    grid-template-columns: minmax(0, 1fr);
  }

  .stage {
    height: auto;
  }

  .frame-wrap {
    flex: none;
    height: min(62vh, 600px);
  }

  .chat {
    height: 520px;
  }

  .top-right {
    gap: 12px;
  }

  .under {
    height: auto;
    min-height: var(--under-h);
  }
}

/* 狭い画面：ヘッダーが詰まらないよう、アプリ名を隠して言語ボタンを小さくする */
@media (max-width: 640px) {
  .brand-name {
    display: none;
  }

  .lang button {
    padding: 5px 8px;
    font-size: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app *,
  .app *::before,
  .app *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* iPhone の Safari は 16px 未満の入力欄を触ると画面を拡大するので、小さい画面では 16px にする */
@media (max-width: 760px) {
  .app textarea,
  .survey .other-input {
    font-size: 16px;
  }
}
</style>
