# The Transformer Architecture

The Transformer is a neural network architecture introduced in the 2017 paper
"Attention Is All You Need" by Vaswani et al. at Google. It dispenses with
recurrence and convolutions entirely, relying solely on attention mechanisms to
model relationships between tokens in a sequence.

## Key components

- **Self-attention:** every token attends to every other token in the sequence,
  allowing the model to capture long-range dependencies in a single step rather
  than propagating information step-by-step as recurrent networks do.
- **Multi-head attention:** the model runs several attention operations in
  parallel ("heads"), each learning to focus on different relationships, then
  concatenates the results.
- **Positional encoding:** because the architecture has no recurrence, sinusoidal
  positional encodings are added to the input embeddings so the model knows the
  order of tokens.
- **Encoder–decoder structure:** the original Transformer has an encoder stack
  that reads the input and a decoder stack that generates the output, though many
  later models use only the encoder (e.g. BERT) or only the decoder (e.g. GPT).

## Why it mattered

Removing recurrence makes training highly parallelizable, so Transformers train
much faster on modern hardware than RNNs and LSTMs. This scalability is the main
reason the Transformer became the foundation for large language models.
