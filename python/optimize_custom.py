import os
import mitsuba as mi

from constants import OUTPUT_DIR, RENDER_DIR, SCENE_DIR

def optimize(config, opt_name, output_dir, ref_image_paths, ref_spp=1024,
             force=False, verbose=False, opt_config_args=None):
    from opt_configs import get_opt_config
    from shape_opt import optimize_shape

    # 1. Render the reference images if needed
    current_output_dir = output_dir
    #os.makedirs(current_output_dir, exist_ok=True)
    #mi.set_log_level(3 if verbose else mi.LogLevel.Warn)
    opt_config, mts_args = get_opt_config(opt_name, opt_config_args)

    # Pass scene name as part of the opt. config
    opt_config.scene = 'dragon'
    #render_reference_images(opt_config, config, ref_spp=ref_spp, force=force, verbose=verbose, mts_args=mts_args)
    #ref_image_paths = copy_reference_images_to_output_dir(opt_config, config, current_output_dir)

    opt_config.sensors = opt_config.sensors[:len(ref_image_paths)]

    # 2. Optimize SDF compared to ref image(s)
    optimize_shape(opt_config, mts_args, ref_image_paths, current_output_dir, config)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='''Reconstructs an object as an SDF''')
    parser.add_argument('output_dir', type=str, help='''Output directory''')
    parser.add_argument('reference_image_paths', type=str, nargs='+', help='''Reference images''')
    parser.add_argument('--optconfigs', '--opt', nargs='+', help='Optimization configurations to run')
    parser.add_argument('--configs', default=['warp'], type=str, nargs='*', help='Method to be used for the optimization. Default: Warp')
    parser.add_argument('--force', action='store_true', help='Force rendering of reference images')
    parser.add_argument('--llvm', action='store_true',
                        help='Force use of LLVM (CPU) mode instead of CUDA/OptiX. This can be useful if compilation times using OptiX are too long.')
    parser.add_argument('--refspp', type=int, default=2048, help='Number of samples per pixel for reference images. Default: 2048')
    parser.add_argument('--verbose', action='store_true', help='Print additional log information')
    args, uargs = parser.parse_known_args()

    use_llvm = args.llvm or not ('cuda_ad_rgb' in mi.variants())
    mi.set_variant('llvm_ad_rgb' if use_llvm else 'cuda_ad_rgb')

    from configs import apply_cmdline_args, get_config
    from opt_configs import is_valid_opt_config, get_opt_config

    if args.optconfigs is None:
        raise ValueError('Must at least specify one opt. config!')

    if any(not is_valid_opt_config(opt) for opt in args.optconfigs):
        raise ValueError(f'Unknown opt config detected: {args.optconfigs}')

    for config_name in args.configs:
        for opt_config in args.optconfigs:
            config = get_config(config_name)
            remaining_args = apply_cmdline_args(config, uargs, return_dict=True)

            optimize(config, opt_config, args.output_dir, args.reference_image_paths, args.refspp, args.force, args.verbose, remaining_args)


if __name__ == '__main__':
    main()