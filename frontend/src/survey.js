// 線上参加者向けアンケート（紙のアンケートと同じ内容）。
// 回答はコードで送る（q1〜q3 は 1〜5、q4〜q6 は選択肢のコード）。日本語・中文は紙版と同じ文言。

export const Q4_CODES = ['face', 'hair', 'clothes', 'body', 'pose', 'background', 'style', 'mood', 'other']
export const Q5_GROUPS = [
  { key: 'start', codes: ['start_what', 'start_how'] },
  { key: 'edit', codes: ['edit_next', 'edit_nochange', 'edit_overchange', 'edit_quality'] },
  { key: 'wait', codes: ['wait_long', 'ui_hard'] },
  { key: 'other', codes: ['other', 'none'] }
]
export const Q6_CODES = ['satisfied', 'gave_up', 'no_idea', 'tired', 'time_up', 'other']

export const SURVEY = {
  ja: {
    toggle: 'オンラインで参加した方は、こちらのアンケートにお答えください',
    closeUnsent: 'アンケートがまだ送信されていません。閉じると、もう回答できません。閉じますか？',
    onsite: '会場で参加した方は、紙のアンケートにお答えください（ここは不要です）。',
    finalLabel: '最後に選んだ画像の番号',
    one: '（1つだけ）',
    many: '（いくつでも）',
    upTo3: '（3つまで）',
    q1: 'これまでに、画像生成AIでキャラクターの画像を作ったことはありますか。',
    q1o: ['作ったことが\nない', '1回だけ\nある', '数回\nある', '以前はよく作ったが\n最近はあまり作らない', '今も\nよく作っている'],
    p2: 'どんなキャラクターにするか、今、イメージはどのくらい決まっていますか。',
    p2o: ['まったく\n決まっていない', 'あまり\n決まっていない', 'どちらとも\nいえない', 'ある程度\n決まっている', 'はっきり\n決まっている'],
    qc: '画像を見ながら作るうちに、作りたいイメージがはっきりしてきましたか。',
    qco: ['まったく\nはっきりしなかった', 'あまり\nはっきりしなかった', 'どちらとも\nいえない', 'ある程度\nはっきりした', 'とても\nはっきりした'],
    q3: '最後に選んだ画像に、どのくらい満足していますか。',
    q3o: ['まったく満足\nしていない', 'あまり満足\nしていない', 'どちらとも\nいえない', 'やや満足\nしている', 'とても満足\nしている'],
    q4: 'キャラクターを作るとき、特にこだわったところはどこですか。',
    q4o: {
      face: '顔・表情', hair: '髪型', clothes: '服装・持ち物', body: '体つき・体型', pose: 'ポーズ・動き',
      background: '背景・世界観', style: '画風・タッチ', mood: '雰囲気・印象', other: 'その他'
    },
    q5: '使っていて困ったことはありましたか。',
    q5g: { start: '作りはじめ', edit: '修正', wait: '待ち・操作', other: 'そのほか' },
    q5o: {
      start_what: '最初にどんなキャラクターを作るか迷った',
      start_how: 'イメージをどう書けばよいか分からなかった',
      edit_next: '次に何を変えるか思いつかなかった',
      edit_nochange: '変えてほしいところが変わらなかった',
      edit_overchange: '変えたくない顔や特徴まで変わった',
      edit_quality: '何度も修正すると画質が悪くなった',
      wait_long: '画像ができるまでの待ち時間が長かった',
      ui_hard: '文字の入力やボタンの操作がしにくかった',
      other: 'その他',
      none: '特に困ったことはなかった'
    },
    q6: 'キャラクター作りを終えた理由を教えてください。',
    q6o: {
      satisfied: '満足できる画像ができたから',
      gave_up: '思いどおりに直せず、あきらめたから',
      no_idea: '次に何を変えるか思いつかなかったから',
      tired: '待つことや操作に疲れたから',
      time_up: '実験の時間が終わったから',
      other: 'その他'
    },
    q7: '気づいたことや、ほしい機能があれば、自由にお書きください。',
    otherPh: '具体的に',
    req: '必須',
    optional: '（任意）',
    required: '必須の質問（3〜7）にお答えください。',
    submit: '送信する',
    sending: '送信しています…',
    sent: 'アンケートを受け付けました。ご協力ありがとうございました。',
    failed: '送信できませんでした。もう一度お試しください：'
  },
  zh: {
    toggle: '线上参与的人，请在这里回答问卷',
    closeUnsent: '问卷还没有提交。关闭后就不能再回答了，确定要关闭吗？',
    onsite: '在现场参与的人，请填写纸质问卷（这里不用填）。',
    finalLabel: '最后选择的图片编号',
    one: '（单选）',
    many: '（可多选）',
    upTo3: '（最多选 3 个）',
    q1: '你以前用图像生成 AI 制作过角色图片吗？',
    q1o: ['没有\n制作过', '只制作过\n1 次', '制作过\n几次', '以前经常制作\n最近不太制作', '现在也\n经常制作'],
    p2: '你想做什么样的角色，现在心里的想法有多明确？',
    p2o: ['完全\n没有想法', '不太\n明确', '说不清', '比较\n明确', '非常\n明确'],
    qc: '一边看图片一边制作，你想要的角色形象变得更清楚了吗？',
    qco: ['完全没有\n变清楚', '不太\n清楚', '说不清', '变得\n比较清楚', '变得\n非常清楚'],
    q3: '你对最后选择的图片有多满意？',
    q3o: ['完全不满意', '不太满意', '说不清', '比较满意', '非常满意'],
    q4: '制作角色时，你特别在意的是哪些地方？',
    q4o: {
      face: '脸・表情', hair: '发型', clothes: '服装・随身物品', body: '体型・身材', pose: '姿势・动作',
      background: '背景・世界观', style: '画风', mood: '气质・印象', other: '其他'
    },
    q5: '使用过程中遇到过困难吗？',
    q5g: { start: '开始制作', edit: '修改', wait: '等待・操作', other: '其他' },
    q5o: {
      start_what: '一开始不知道要做什么样的角色',
      start_how: '不知道该怎样描述自己的想象',
      edit_next: '想不出接下来要改什么',
      edit_nochange: '想改的地方没有改变',
      edit_overchange: '不想改的脸或特征也被改变了',
      edit_quality: '修改多次后画质变差了',
      wait_long: '等待图片生成的时间太长',
      ui_hard: '输入文字或操作按钮不方便',
      other: '其他',
      none: '没有特别的困难'
    },
    q6: '请告诉我们你结束角色制作的原因。',
    q6o: {
      satisfied: '做出了满意的图片',
      gave_up: '没能按想法修改，所以放弃了',
      no_idea: '想不出接下来要改什么',
      tired: '等待或操作让人疲倦',
      time_up: '实验时间到了',
      other: '其他'
    },
    q7: '如果有注意到的地方或希望增加的功能，请自由填写。',
    otherPh: '请具体填写',
    req: '必答',
    optional: '（选填）',
    required: '请回答必答题（3〜7）。',
    submit: '提交',
    sending: '正在提交…',
    sent: '问卷已提交。感谢你的配合。',
    failed: '提交失败，请再试一次：'
  },
  en: {
    toggle: 'If you took part online, please answer the questionnaire here',
    closeUnsent: 'The questionnaire has not been sent. If you close this, you cannot answer it any more. Close anyway?',
    onsite: 'If you took part on site, please use the paper questionnaire (no need to fill this in).',
    finalLabel: 'Number of the final image you chose',
    one: '(choose one)',
    many: '(choose all that apply)',
    upTo3: '(up to 3)',
    q1: 'Have you ever made character images with an image-generation AI?',
    q1o: ['Never', 'Once', 'A few times', 'Often before, rarely now', 'Often, even now'],
    p2: 'How clear is your idea of the character right now?',
    p2o: ['Not at all\nclear', 'Not very\nclear', 'Neither', 'Fairly\nclear', 'Very\nclear'],
    qc: 'While making it and looking at the images, did your idea of the character become clearer?',
    qco: ['Not at all', 'Not really', 'Neither', 'Somewhat\nclearer', 'Much\nclearer'],
    q3: 'How satisfied are you with the final image you chose?',
    q3o: ['Not at all satisfied', 'Not very satisfied', 'Neither', 'Somewhat satisfied', 'Very satisfied'],
    q4: 'What did you care about most when making the character?',
    q4o: {
      face: 'Face / expression', hair: 'Hairstyle', clothes: 'Clothes / items', body: 'Body type',
      pose: 'Pose / movement', background: 'Background / setting', style: 'Art style',
      mood: 'Mood / impression', other: 'Other'
    },
    q5: 'Did you have any difficulties?',
    q5g: { start: 'Getting started', edit: 'Editing', wait: 'Waiting / controls', other: 'Other' },
    q5o: {
      start_what: 'I was unsure what kind of character to make',
      start_how: 'I did not know how to describe what I imagined',
      edit_next: 'I could not think of what to change next',
      edit_nochange: 'What I wanted to change did not change',
      edit_overchange: 'Things I wanted to keep (face, features) changed too',
      edit_quality: 'Image quality got worse after many edits',
      wait_long: 'Waiting for images took too long',
      ui_hard: 'Typing or using the buttons was hard',
      other: 'Other',
      none: 'No particular difficulties'
    },
    q6: 'Why did you finish making the character?',
    q6o: {
      satisfied: 'I got an image I was satisfied with',
      gave_up: 'I gave up because I could not change it as I wanted',
      no_idea: 'I could not think of what to change next',
      tired: 'I got tired of waiting or operating',
      time_up: 'The time was up',
      other: 'Other'
    },
    q7: 'Any comments, or features you would like? (free text)',
    otherPh: 'Please specify',
    req: 'Required',
    optional: '(optional)',
    required: 'Please answer the required questions (3–7).',
    submit: 'Submit',
    sending: 'Sending…',
    sent: 'Thank you. Your answers have been received.',
    failed: 'Could not send. Please try again: '
  }
}
