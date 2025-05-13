#!/bin/bash
export PRETRAINED_MODELS_HOME=/Users/liuqingwen/Firm/Private/work-space/ai-coding/pinyin-reading-companion/models
export PPNLP_HOME=$PRETRAINED_MODELS_HOME
export PADDLESPEECH_HOME=$PRETRAINED_MODELS_HOME
export PADDLESPEECH_DISABLE_DOWNLOAD=1
export PPNLP_DISABLE_DOWNLOAD=1
export G2P_MODEL_PATH=$PRETRAINED_MODELS_HOME/paddlespeech/G2PWModel
python app.py