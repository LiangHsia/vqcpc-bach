"""
@author: Gaetan Hadjeres
"""
import importlib
import os
import shutil
from datetime import datetime

import click
import torch

from VQCPCB.data.data_processor import DataProcessor
from VQCPCB.getters import get_dataloader_generator, get_encoder, get_decoder, get_data_processor


@click.command()
@click.option('-t', '--train', is_flag=True)
@click.option('-l', '--load', is_flag=True)
@click.option('-oe', '--overfitted_encoder', is_flag=True,
              help='Load over-fitted weights for the encoder')
@click.option('-o', '--overfitted', is_flag=True,
              help='Load over-fitted weights for the decoder instead of early-stopped.'
                   'Only used with -l')
@click.option('-c', '--config', type=click.Path(exists=True))
@click.option('-r', '--reharmonization', is_flag=True)
@click.option('--code_juxtaposition', is_flag=True)
@click.option('-n', '--num_workers', type=int, default=0)
def main(train,
         load,
         overfitted_encoder,
         overfitted,
         config,
         reharmonization,
         code_juxtaposition,
         num_workers
         ):
    # Use all gpus available
    gpu_ids = [int(gpu) for gpu in range(torch.cuda.device_count())]
    print(f'Using GPUs {gpu_ids}')
    if len(gpu_ids) == 0:
        device = 'cpu'
    else:
        device = 'cuda'

    # Load config
    config_path = config
    config_module_name = os.path.splitext(config)[0].replace('/', '.')
    config = importlib.import_module(config_module_name).config

    # compute time stamp
    if config['timestamp'] is not None:
        timestamp = config['timestamp']
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        config['timestamp'] = timestamp

    if load:
        model_dir = os.path.dirname(config_path)
    else:
        model_dir = f'models/{config["savename"]}_{timestamp}'

    # ==== Load encoders ====
    # load stack of encoders from top-most encoder (lastly trained)
    config_encoder_path = config['config_encoder']
    if config_encoder_path is None:
        # Load any encoder w/ 16 code
        config_encoder_path = 'VQCPCB/configs/encoder_random.py'
    config_encoder_module_name = os.path.splitext(config_encoder_path)[0].replace('/', '.')
    config_encoder = importlib.import_module(config_encoder_module_name).config
    config_encoder['quantizer_kwargs']['initialize'] = False
    if config['config_encoder'] is None:
        model_dir_encoder = None
    else:
        model_dir_encoder = os.path.dirname(config_encoder_path)
    dataloader_generator = get_dataloader_generator(
        training_method=config_encoder['training_method'],
        dataloader_generator_kwargs=config_encoder['dataloader_generator_kwargs'],
    )
    encoder = get_encoder(model_dir=model_dir_encoder,
                          dataloader_generator=dataloader_generator,
                          config=config_encoder
                          )
    if config['config_encoder'] is not None:
        if overfitted_encoder:
            encoder.load(early_stopped=False, device=device)
        else:
            encoder.load(early_stopped=True, device=device)

    # === Decoder ====
    dataloader_generator = get_dataloader_generator(
        training_method=config['training_method'],
        dataloader_generator_kwargs=config['dataloader_generator_kwargs']
    )

    data_processor: DataProcessor = get_data_processor(
        dataloader_generator=dataloader_generator,
        data_processor_kwargs=config['data_processor_kwargs']
    )

    decoder = get_decoder(
        model_dir=model_dir,
        dataloader_generator=dataloader_generator,
        data_processor=data_processor,
        encoder=encoder,
        decoder_type=config['decoder_type'],
        decoder_kwargs=config['decoder_kwargs']
    )

    if load:
        if overfitted:
            decoder.load(early_stopped=False, device=device)
        else:
            decoder.load(early_stopped=True, device=device)
        decoder.to(device)

    if train:
        # Copy .py config file in the save directory before training
        if not load:
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            shutil.copy(config_path, f'{model_dir}/config.py')
        decoder.to(device)
        decoder.train_model(
            batch_size=config['batch_size'],
            num_batches=config['num_batches'],
            num_epochs=config['num_epochs'],
            lr=config['lr'],
            schedule_lr=config['schedule_lr'],
            plot=True,
            num_workers=num_workers
        )

    num_examples = 3
    for _ in range(num_examples):
        if code_juxtaposition:
            scores = decoder.generate(
                temperature=1.0,
                top_p=0.8,
                top_k=0,
                batch_size=3,
                seed_set='val',
                plot_attentions=False,
                code_juxtaposition=True
            )

        scores = decoder.generate(temperature=1.0,
                                  top_p=0.8,
                                  top_k=0,
                                  batch_size=3,
                                  seed_set='val',
                                  plot_attentions=False,
                                  code_juxtaposition=False)
        # for score in scores:
        #     score.show()

    if reharmonization:
        scores = decoder.generate_reharmonisation(
            temperature=1.0,
            top_p=0.8,
            top_k=0,
            num_reharmonisations=3)
    # for score in scores:
    #     score.show()


if __name__ == '__main__':
    main()
