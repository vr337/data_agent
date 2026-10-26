<template>
  <div class="shell">
    <!-- 左侧说明栏：交代系统如何工作，属于真实流程，不是装饰 -->
    <aside class="rail">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true"></span>
        <div>
          <div class="brand-name">问数</div>
          <div class="brand-sub">数据问答工作台</div>
        </div>
      </div>

      <section class="rail-block">
        <h2 class="rail-title">它怎么工作</h2>
        <ol class="flow">
          <li class="flow-item"><span class="flow-num">01</span><span>关键字提取</span></li>
          <li class="flow-item"><span class="flow-num">02</span><span>三路召回：字段、指标、字段值</span></li>
          <li class="flow-item"><span class="flow-num">03</span><span>召回信息合并</span></li>
          <li class="flow-item"><span class="flow-num">04</span><span>过滤指标与表</span></li>
          <li class="flow-item"><span class="flow-num">05</span><span>补充日期与数据库信息</span></li>
          <li class="flow-item"><span class="flow-num">06</span><span>生成 SQL</span></li>
          <li class="flow-item"><span class="flow-num">07</span><span>校验，未通过则自动矫正</span></li>
          <li class="flow-item"><span class="flow-num">08</span><span>执行 SQL 并返回结果</span></li>
        </ol>
      </section>

      <div class="rail-foot">
        <h2 class="rail-title">数据来源</h2>
        <ul class="sources">
          <li><span class="source-key">MySQL</span><span>元数据库与数据仓库</span></li>
          <li><span class="source-key">Qdrant</span><span>字段与指标向量检索</span></li>
          <li><span class="source-key">ES</span><span>字段值检索</span></li>
        </ul>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <span class="topbar-mark" aria-hidden="true"></span>
          <span class="topbar-name">问数</span>
          <span class="topbar-sep" aria-hidden="true"></span>
          <span class="topbar-title">新对话</span>
        </div>
        <div class="topbar-right">
          <button
            v-if="messages.length"
            type="button"
            class="ghost-btn"
            :disabled="loading"
            @click="resetConversation"
          >
            清空对话
          </button>
          <span class="status" :class="loading ? 'is-busy' : 'is-idle'" role="status">
            <span class="status-dot" aria-hidden="true"></span>
            {{ loading ? "执行中" : "就绪" }}
          </span>
        </div>
      </header>

      <div ref="messagesEl" class="transcript">
        <div class="thread">
          <!-- 空态：第一次进来看到的东西 -->
          <section v-if="!messages.length" class="intro">
            <h1 class="intro-title">问一句，<br />看到数。</h1>
            <p class="intro-lead">
              用中文描述你想知道的事。系统会自己找到相关的表和指标，写出 SQL，再把结果带回来。
            </p>

            <ul class="samples">
              <li v-for="sample in samples" :key="sample">
                <button type="button" class="sample" @click="useSample(sample)">
                  <span>{{ sample }}</span>
                  <span class="sample-hint">填入</span>
                </button>
              </li>
            </ul>
          </section>

          <!-- 对话 -->
          <template v-else>
            <template v-for="(msg, index) in messages" :key="index">
              <div v-if="msg.role === 'user'" class="msg msg-user">
                <div class="user-bubble">{{ msg.content }}</div>
              </div>

              <div v-else-if="msg.type === 'text'" class="msg msg-assistant">
                <p class="plain-text">{{ msg.content }}</p>
              </div>

              <div v-else-if="msg.type === 'steps'" class="msg msg-assistant">
                <div class="block-label">执行轨迹</div>
                <div v-if="!msg.steps.length" class="trace-pending">正在理解问题…</div>
                <ol v-else class="trace">
                  <li
                    v-for="(step, sIdx) in msg.steps"
                    :key="sIdx"
                    class="step"
                    :class="'is-' + step.status"
                  >
                    <span class="step-dot" aria-hidden="true"></span>
                    <span class="step-text">{{ step.text }}</span>
                  </li>
                </ol>
              </div>

              <div v-else-if="msg.type === 'table'" class="msg msg-assistant">
                <div class="block-label">查询结果</div>
                <div class="result">
                  <div class="result-head">
                    <h3 class="result-title">
                      {{ msg.rows.length ? "返回数据" : "没有返回数据" }}
                    </h3>
                    <span class="result-meta">
                      {{ msg.rows.length }} 行 × {{ msg.columns.length }} 列
                    </span>
                  </div>

                  <div v-if="!msg.rows.length" class="result-empty">
                    这次查询没有命中任何行。可以换一个时间范围或筛选条件再问一次。
                  </div>

                  <div v-else class="table-scroll">
                    <table class="result-table">
                      <thead>
                        <tr>
                          <th
                            v-for="col in msg.columns"
                            :key="col"
                            scope="col"
                            :class="{ num: msg.numeric.includes(col) }"
                          >
                            {{ col }}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, rIdx) in msg.rows" :key="rIdx">
                          <td
                            v-for="col in msg.columns"
                            :key="col"
                            :class="{ num: msg.numeric.includes(col) }"
                          >
                            {{ cellText(row[col]) }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div v-else-if="msg.type === 'error'" class="msg msg-assistant">
                <div class="block-label">没能完成</div>
                <div class="err-box">{{ msg.content }}</div>
              </div>
            </template>
          </template>
        </div>
      </div>

      <div class="composer">
        <form class="composer-box" @submit.prevent="sendQuestion">
          <textarea
            ref="inputEl"
            v-model="question"
            class="composer-input"
            rows="1"
            placeholder="问点什么…"
            aria-label="输入你的问题"
            @input="autoGrow"
            @keydown="onKeydown"
          ></textarea>
          <button
            type="submit"
            class="send-btn"
            :disabled="loading || !question.trim()"
          >
            {{ loading ? "执行中" : "发送" }}
          </button>
        </form>
        <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { nextTick, ref } from "vue";

const API_URL = "/api/query";

const samples = [
  "上个月华东地区的 GMV 是多少？",
  "各品类的订单金额排名前五",
  "男女会员的平均订单金额对比",
];

const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);
const inputEl = ref(null);

function scrollToBottom() {
  const el = messagesEl.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

function autoGrow() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

function useSample(text) {
  question.value = text;
  nextTick(() => {
    inputEl.value?.focus();
    autoGrow();
  });
}

function resetConversation() {
  if (loading.value) return;
  messages.value = [];
  question.value = "";
  nextTick(() => {
    autoGrow();
    inputEl.value?.focus();
  });
}

// 中文输入法确认候选词时也会触发 Enter，需要避开
function onKeydown(event) {
  if (event.isComposing) return;
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendQuestion();
  }
}

function cellText(value) {
  if (value === null || value === undefined || value === "") return "—";
  return value;
}

function isNumericColumn(column, rows) {
  let seen = false;
  for (const row of rows) {
    const value = row[column];
    if (value === null || value === undefined || value === "") continue;
    if (typeof value === "number") {
      seen = true;
      continue;
    }
    if (typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value.trim())) {
      seen = true;
      continue;
    }
    return false;
  }
  return seen;
}

async function sendQuestion() {
  if (!question.value.trim() || loading.value) return;

  const q = question.value;
  question.value = "";
  loading.value = true;

  messages.value.push({ role: "user", type: "text", content: q });

  const stepIndex =
    messages.value.push({
      role: "assistant",
      type: "steps",
      steps: [],
    }) - 1;

  await nextTick();
  autoGrow();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q }),
    });

    if (!response.body) throw new Error("服务器未返回流");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;

        let data;
        try {
          data = JSON.parse(line.replace(/^data:\s*/, ""));
        } catch {
          continue;
        }

        const steps = messages.value[stepIndex]?.steps ?? [];

        if (data.stage) {
          const last = steps.at(-1);
          if (last && last.status === "running") last.status = "success";
          steps.push({ text: data.stage, status: "running" });
        } else if (data.error) {
          const last = steps.at(-1);
          if (last) last.status = "error";
          messages.value.push({
            role: "assistant",
            type: "error",
            content: data.error,
          });
        } else if (Array.isArray(data.result)) {
          const last = steps.at(-1);
          if (last) last.status = "success";
          const columns = Object.keys(data.result[0] || {});
          messages.value.push({
            role: "assistant",
            type: "table",
            columns,
            rows: data.result,
            numeric: columns.filter((col) => isNumericColumn(col, data.result)),
          });
        }

        await nextTick();
        scrollToBottom();
      }
    }
  } catch (e) {
    messages.value.push({
      role: "assistant",
      type: "error",
      content: e?.message || "请求失败",
    });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}
</script>

<style scoped>
.shell {
  display: flex;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--paper);
}

/* ---------- 左侧说明栏 ---------- */
.rail {
  width: 272px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 26px 22px 22px;
  background: var(--sidebar);
  border-right: 1px solid var(--line);
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 40px;
}

.brand-mark {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  background: var(--accent);
  flex-shrink: 0;
  box-shadow: inset 0 -6px 0 rgba(255, 255, 255, 0.22);
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.brand-sub {
  margin-top: 1px;
  font-size: 12px;
  color: var(--ink-faint);
}

.rail-block {
  margin-bottom: 36px;
}

.rail-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-faint);
  margin-bottom: 12px;
}

.flow {
  display: flex;
  flex-direction: column;
}

.flow-item {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 6px;
  padding: 6px 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink-soft);
}

.flow-num {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faint);
  padding-top: 2px;
}

.rail-foot {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}

.sources {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sources li {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.source-key {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--ink);
}

.sources li span:last-child {
  font-size: 12px;
  color: var(--ink-faint);
}

/* ---------- 主区域 ---------- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--paper);
}

.topbar {
  flex-shrink: 0;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 28px;
  border-bottom: 1px solid var(--line);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.topbar-mark {
  display: none;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  background: var(--accent);
  box-shadow: inset 0 -5px 0 rgba(255, 255, 255, 0.22);
}

.topbar-name {
  display: none;
  font-size: 14px;
  font-weight: 600;
}

.topbar-sep {
  display: none;
  width: 1px;
  height: 14px;
  background: var(--line-strong);
}

.topbar-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ghost-btn {
  padding: 6px 12px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: transparent;
  font-size: 12.5px;
  color: var(--ink-soft);
  transition: border-color 0.15s ease, color 0.15s ease;
}

.ghost-btn:hover:not(:disabled) {
  border-color: var(--ink-soft);
  color: var(--ink);
}

.ghost-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--ink-soft);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
}

.status.is-busy .status-dot {
  background: var(--accent);
  animation: pulse 1.1s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.25;
  }
}

/* ---------- 滚动区 ---------- */
.transcript {
  flex: 1;
  overflow-y: auto;
  padding: 36px 32px 28px;
}

.thread {
  max-width: 880px;
  margin: 0 auto;
}

/* ---------- 空态 ---------- */
.intro {
  max-width: 620px;
  margin: clamp(32px, 11vh, 128px) auto 0;
}

.intro-title {
  font-size: clamp(36px, 4.6vw, 58px);
  line-height: 1.14;
  letter-spacing: -0.02em;
  font-weight: 600;
}

.intro-lead {
  margin-top: 22px;
  max-width: 44ch;
  font-size: 15.5px;
  line-height: 1.8;
  color: var(--ink-soft);
}

.samples {
  margin-top: 44px;
  border-top: 1px solid var(--line);
}

.samples li {
  border-bottom: 1px solid var(--line);
}

.sample {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 12px 16px 12px;
  border: none;
  border-left: 2px solid transparent;
  background: transparent;
  text-align: left;
  font-size: 14.5px;
  color: var(--ink);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.sample:hover {
  border-left-color: var(--accent);
  background: rgba(255, 255, 255, 0.5);
}

.sample-hint {
  font-size: 12px;
  color: var(--ink-faint);
  opacity: 0;
  transition: opacity 0.15s ease;
}

.sample:hover .sample-hint,
.sample:focus-visible .sample-hint {
  opacity: 1;
}

/* ---------- 对话 ---------- */
.msg {
  margin-bottom: 16px;
}

.msg-user {
  display: flex;
  justify-content: flex-end;
  margin: 26px 0 24px;
}

.user-bubble {
  max-width: min(620px, 84%);
  padding: 12px 16px;
  border-radius: 12px 12px 4px 12px;
  background: var(--ink);
  color: #f6f5f1;
  font-size: 14.5px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.plain-text {
  font-size: 14.5px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.block-label {
  font-size: 12px;
  color: var(--ink-faint);
  margin-bottom: 10px;
}

.trace-pending {
  font-size: 13.5px;
  color: var(--ink-faint);
  padding-left: 1px;
}

.trace {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-left: 4px;
  padding-left: 18px;
  border-left: 1px solid var(--line);
}

.step {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13.5px;
  color: var(--ink-soft);
  position: relative;
}

.step-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--line-strong);
  margin-left: -22px;
  box-shadow: 0 0 0 4px var(--paper);
}

.step.is-running .step-dot {
  background: var(--accent);
  animation: pulse 1.1s ease-in-out infinite;
}

.step.is-running .step-text {
  color: var(--ink);
}

.step.is-success .step-dot {
  background: var(--ok);
}

.step.is-error .step-dot {
  background: var(--bad);
}

.step.is-error .step-text {
  color: var(--bad);
}

/* ---------- 结果表 ---------- */
.result {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
  overflow: hidden;
}

.result-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.result-title {
  font-size: 13px;
  font-weight: 600;
}

.result-meta {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--ink-faint);
  white-space: nowrap;
}

.result-empty {
  padding: 18px 16px;
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--ink-soft);
}

.table-scroll {
  overflow: auto;
  max-height: 440px;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
}

.result-table th,
.result-table td {
  padding: 9px 16px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid #eceae3;
  font-variant-numeric: tabular-nums;
}

.result-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--surface);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-soft);
  border-bottom: 1px solid var(--line-strong);
}

.result-table th.num,
.result-table td.num {
  text-align: right;
}

.result-table tbody tr:hover {
  background: #f6f5f0;
}

.result-table tbody tr:last-child td {
  border-bottom: none;
}

/* ---------- 错误 ---------- */
.err-box {
  padding: 14px 16px;
  border: 1px solid #f0c9c6;
  border-radius: 10px;
  background: var(--bad-soft);
  color: #7d1b15;
  font-size: 13.5px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

/* ---------- 输入区 ---------- */
.composer {
  flex-shrink: 0;
  padding: 14px 32px 22px;
  background: var(--paper);
  border-top: 1px solid transparent;
}

.composer-box {
  max-width: 880px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 8px 8px 16px;
  border: 1px solid var(--line-strong);
  border-radius: 12px;
  background: var(--surface);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.composer-box:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.composer-input {
  flex: 1;
  min-width: 0;
  max-height: 160px;
  padding: 8px 0;
  border: none;
  outline: none;
  background: transparent;
  resize: none;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ink);
}

.composer-input::placeholder {
  color: var(--ink-faint);
}

.send-btn {
  flex-shrink: 0;
  padding: 9px 18px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: #fff;
  font-size: 13.5px;
  font-weight: 500;
  transition: background-color 0.15s ease;
}

.send-btn:hover:not(:disabled) {
  background: #262cb8;
}

.send-btn:disabled {
  background: var(--line-strong);
  color: var(--surface);
  cursor: not-allowed;
}

.composer-hint {
  max-width: 880px;
  margin: 8px auto 0;
  font-size: 11.5px;
  color: var(--ink-faint);
}

/* ---------- 窄屏 ---------- */
@media (max-width: 960px) {
  .rail {
    display: none;
  }

  .topbar {
    padding: 0 18px;
  }

  .topbar-mark,
  .topbar-name,
  .topbar-sep {
    display: block;
  }

  .transcript {
    padding: 24px 18px 20px;
  }

  .intro {
    margin-top: 40px;
  }

  .composer {
    padding: 12px 18px 16px;
  }

  .composer-hint {
    display: none;
  }
}

@media (max-width: 520px) {
  .topbar-title {
    display: none;
  }

  .msg-user {
    margin: 20px 0;
  }

  .user-bubble {
    max-width: 92%;
  }
}
</style>
