from pathlib import Path

subdivision = 4
num_beats = 2
num_voices = 4
num_tokens_per_block = num_beats * subdivision * num_voices
num_block_left = 6
num_block_right = 6
sequences_size = 12

config = {
    'training_method': 'vqcpc',  # vqcpc or student

    # ======== Dataloader ======
    'dataloader_generator_kwargs': dict(num_tokens_per_block=num_tokens_per_block,
                                        num_blocks_left=num_block_left,
                                        num_blocks_right=num_block_right,
                                        negative_sampling_method='same_sequence',  # random or same_sequence
                                        num_negative_samples=15,            # useless in the same_sequence case
                                        sequences_size=sequences_size,      # used only for visualising clusters
                                        ),
    'subdivision': subdivision,  # Number of frame per quarter note

    # ======== Encoder =========
    # --- DataProcessor ---
    'data_processor_kwargs': dict(
        embedding_size=32
    ),
    # --- Downscaler ---
    'downscaler_type': 'lstm_downscaler',
    'downscaler_kwargs': dict(
        # DCPC uses a Transformer
        downscale_factors=[num_tokens_per_block],
        hidden_size=512,
        num_layers=2,
        dropout=0.1,
        bidirectional=True
    ),
    # --- Quantizer ---
    'quantizer_type': 'commitment',
    'quantizer_kwargs': dict(
        codebook_size=16,
        codebook_dim=3,
        commitment_cost=0.25,
        use_batch_norm=False,
        squared_l2_norm=True
        # add corrupt indices
    ),
    # --- Upscaler ---
    'upscaler_type': 'mlp_upscaler',  # mlp_upscaler
    # 'upscaler_type': None,  # mlp_upscaler
    'upscaler_kwargs': dict(
        # DCPC uses a Transformer
        output_dim=32,
        hidden_size=512,
        dropout=0.1
    ),

    # ======== AuxiliaryNetworks =====
    'auxiliary_networks_kwargs': {
        'quantization_weighting': 1.0,
        'c_net_kwargs': dict(
            output_dim=32,
            hidden_size=512,
            num_layers=2,
            dropout=0.1,
            bidirectional=False,
        ),
    },

    # ======== Training ========
    'lr': 1e-4,
    'schedule_lr': False,
    'batch_size': 32,
    'num_batches': 512,
    'num_epochs': 20000,
    'quantizer_regularization': dict(
        corrupt_labels=False
    ),

    # ======== model ID ========
    'timestamp': None,
    'savename': Path(__file__).stem,
}
