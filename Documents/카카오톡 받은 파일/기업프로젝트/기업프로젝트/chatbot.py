import json
from flask import Flask, request, jsonify
from transformers import (
    AutoModelForSeq2SeqLM, AutoTokenizer,
    Trainer, TrainingArguments, DataCollatorForSeq2Seq
)
from datasets import load_dataset
import torch
import os

app = Flask(__name__)

# ✅ 다국어 번역 모델 파인튜닝 준비
TRANSLATION_MODEL_NAME = "Helsinki-NLP/opus-mt-en-ko"
OUTPUT_DIR = "./trained_mt_model"

# ✅ 1. 데이터 로딩 및 전처리 (JSONL 파일 필요)
def load_translation_dataset(jsonl_path):
    dataset = load_dataset("json", data_files=jsonl_path, split="train")
    dataset = dataset.map(lambda x: {"translation": {"en": x["eng"], "ko": x["kor"]}})
    return dataset

# ✅ 2. 모델, 토크나이저, 데이터 콜레이터 로딩
def prepare_training():
    tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL_NAME)
    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
    return tokenizer, model, data_collator

# ✅ 3. 학습 함수
def train_translation_model(dataset_path):
    dataset = load_translation_dataset(dataset_path)
    tokenizer, model, data_collator = prepare_training()

    def preprocess_function(examples):
        inputs = examples["translation"]["en"]
        targets = examples["translation"]["ko"]
        model_inputs = tokenizer(inputs, max_length=128, truncation=True, padding="max_length")
        labels = tokenizer(targets, max_length=128, truncation=True, padding="max_length")
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=4,
        num_train_epochs=3,
        logging_dir="./logs",
        save_steps=500,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        evaluation_strategy="no"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

# ✅ 4. 번역 모델 로딩
def load_mt_model(src, tgt):
    model_name = f"Helsinki-NLP/opus-mt-{src}-{tgt}"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

# ✅ 5. 번역 실행 함수
def translate(text, tokenizer, model):
    tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        output = model.generate(**tokens, max_length=128)
    return tokenizer.decode(output[0], skip_special_tokens=True)

# ✅ 6. KoGPT 챗봇 응답 (가상 함수)
def kogpt_response(korean_input):
    return f"[KoGPT 응답] {korean_input}"

# ✅ 7. 전체 다국어 챗봇 API
@app.route('/chat', methods=['POST'])
def multilingual_chat():
    data = request.json
    user_input = data['message']
    source_lang = data['lang']  # 예: 'en', 'ja', 'zh', 'vi', 'id'

    tokenizer_in, model_in = load_mt_model(source_lang, 'ko')
    korean_input = translate(user_input, tokenizer_in, model_in)

    kogpt_output = kogpt_response(korean_input)

    tokenizer_out, model_out = load_mt_model('ko', source_lang)
    final_output = translate(kogpt_output, tokenizer_out, model_out)

    return jsonify({
        'input_lang': source_lang,
        'translated_input': korean_input,
        'kogpt_output': kogpt_output,
        'translated_output': final_output
    })

if __name__ == '__main__':
    # 학습 시작하려면 아래 줄 주석 해제
    train_translation_model("parallel_finance_translation_data.jsonl")
    app.run(debug=True, port=5001)