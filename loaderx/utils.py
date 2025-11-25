import json
import shutil
from tqdm import tqdm
from pathlib import Path
from array_record.python.array_record_module import ArrayRecordWriter

def converter(data, output_dir, replace=False, blocksize=4096, ar_options= "group_size:1,zstd"):
    """
    Convert a NumPy array to an ArrayRecord format.

    Args:
        data : numpy.ndarray
            The input data to be converted.
        output_dir : str
            The output directory where the ArrayRecord files will be saved.
        replace : bool, optional
            If True, the output directory will be deleted if it already exists.
            Defaults to False.
        blocksize : int, optional
            The number of records to write to each ArrayRecord file.
            Defaults to 4096.
        ar_options : str, optional
            The options to be passed to the ArrayRecordWriter.
            Defaults to "group_size:1,zstd".
    """
    output_dir = Path(output_dir)
    if output_dir.exists():
        if replace:
            shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        elif any(output_dir.iterdir()):
            raise ValueError(f"output_dir is not empty: {output_dir}")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    meta = {"length": data.shape[0], "shape": data.shape[1:], "dtype": str(data.dtype), "blocks":[]}

    bidx = 0
    writer = None
    for i,tmp in enumerate(tqdm(data)):
        if i % blocksize == 0:
            if writer is not None:
                writer.close()
            writer = ArrayRecordWriter(str(output_dir / f"{bidx}.ar"), options=ar_options)
            meta["blocks"].append(f"{bidx}.ar")
            bidx += 1
        writer.write(tmp.tobytes())
    writer.close()

    with open(output_dir / "meta.json", 'w', encoding='utf-8') as f:
        json.dump(meta, f)