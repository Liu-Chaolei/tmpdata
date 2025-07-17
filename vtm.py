import subprocess
import json
import re
import os
import shlex
from collections import OrderedDict

# python vtm.py
# VTM编码器命令列表
VTM_version = "VTM-17.0"
cfg_path = f"/home/liuchaolei/Video-Coder/{VTM_version}/cfg/encoder_intra_vtm.cfg"
quality = 51
output_root = "/data/ssd/liuchaolei/results/reconstruct"
output_json_dir = "/home/liuchaolei/Toolbox/VTM-17.0"
json_cfg_path = "/home/liuchaolei/Toolbox/HEVC_B.json"

with open(json_cfg_path, 'r') as json_cfg:
    data = json.load(json_cfg)

for dataset_name in data["test_classes"].keys():
    results = {}
    for video_name, info in data["test_classes"][dataset_name]["sequences"].items():
        input_dir = data["root_path"] + data["test_classes"][dataset_name]["base_path"] + "/"
        FrameRate = int(video_name.split('_')[-1].split('.')[0])
        base_name = video_name.replace('.yuv', '')
        SourceWidth = info["width"]
        SourceHeight = info["height"]
        FramesToBeEncoded = info["frames"]
        output_dir = f"{output_root}/{VTM_version}/{dataset_name}/yuv/{str(quality)}/"
        output_json = f"{output_json_dir}/{dataset_name}/{str(quality)}.json"
        cmd = (
            f"/home/liuchaolei/Video-Coder/{VTM_version}/bin/umake/gcc-9.5/x86_64/release/EncoderApp -c {cfg_path} -q {quality} "
            f"--InputFile={input_dir}{base_name}.yuv "
            f"--FrameRate={FrameRate} --FramesToBeEncoded={FramesToBeEncoded} "
            f"--SourceWidth={SourceWidth} --SourceHeight={SourceHeight} "
            f"--BitstreamFile={output_dir}{base_name}.bin "
            f"--ReconFile={output_dir}{base_name}.yuv"
        )

        print(f"开始编码: {video_name}...")
        try:
            # 执行命令并捕获输出
            result = subprocess.run(
                cmd.split(), 
                capture_output=True, 
                text=True,
                check=True
            )
            output = result.stdout

            bitrate_match = re.search(
                r"Total Frames[^\n]*\n\s*\d+\s+\w\s+(\d+\.\d+)", 
                output
            )
            # 提取码率
            if bitrate_match:
                bitrate_kbps = float(bitrate_match.group(1))
                print(f"成功提取码率: {bitrate_kbps} kbps")
            else:
                print("警告: 未找到码率信息")
                bitrate_kbps = None
            
            results[video_name] = bitrate_kbps
            
        except Exception as e:
            print(f"编码失败: {str(e)}")
            results[video_name] = None

    # ===== 保存结果 =====
    with open(output_json, "w") as f:
        json.dump(results, f, indent=4)

    print("\n✓ 编码完成! 码率结果:")
    for video, rate in results.items():
        status = f"{rate} kbps" if rate is not None else "提取失败"
        print(f"  - {video}: {status}")
