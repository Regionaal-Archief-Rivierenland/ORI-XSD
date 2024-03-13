#!/usr/bin/python

from datetime import datetime, timedelta
import sys
import subprocess
import xml.etree.ElementTree as ET
import argparse

def timestamp_to_seconds(timestamp):
    # Assuming the timestamp is in the format HH:MM:SS
    time_parts = list(map(float, timestamp.split(':')))

    # Create a timedelta object with the given time parts
    delta = timedelta(hours=time_parts[0], minutes=time_parts[1], seconds=time_parts[2])
    # Use total_seconds() to get the total duration in seconds
    total_seconds = int(delta.total_seconds())

    return total_seconds

parser = argparse.ArgumentParser(description="Add chapter markers from ORI.xml to video file INPUT.vid")
parser.add_argument("ori_xml", metavar="ORI.xml", help="ORI XML file from which timestamps should be read")
parser.add_argument("vid", metavar="VIDEO.vid", help="Video to which timestamps/chapter markers should be added")

args = parser.parse_args()

xml_file = args.ori_xml
vid = args.vid

xml_root = ET.parse(xml_file).getroot()
ns = {'ori' : 'https://vng.nl/projecten/open-raadsinformatie'}

starttijden = xml_root.findall(".//ori:agendapunt/ori:starttijd", ns)
eindtijden = xml_root.findall(".//ori:agendapunt/ori:eindtijd", ns)
titels = xml_root.findall(".//ori:agendapunt/ori:agendapuntTitel", ns)
vergadering_naam = xml_root.find(".//ori:vergadering/ori:naam", ns).text
vergadering_organisator = xml_root.find(".//ori:vergadering/ori:georganiseerdDoorGremium/ori:gremiumNaam", ns).text

with open("/tmp/FFMETADATAFILE.txt", 'w+') as f:
    print(";FFMETADATA1", file=f)

    if vergadering_naam:
        print(f"title={vergadering_naam.strip()}", file=f)
    if vergadering_organisator:
        print(f"artist={vergadering_organisator.strip()}", file=f)

    for start, end, t, in zip(starttijden, eindtijden, titels):
        start = timestamp_to_seconds(start.text)
        end = timestamp_to_seconds(end.text)
        print(f"""[CHAPTER]
title={t.text}
TIMEBASE=1/1
START={start}
END={end}
""", file=f, end="\n")

    out, ext = os.path.splitext(os.path.basename(vid))
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        vid,
        "-f",
        "ffmetadata",
        "-i",
        f.name,
        "-map",
        "0:v",
        "-map",
        "0:a",
        "-map_metadata",
        '1',
        "-c",
        "copy",
        out + "-markers" + ext
    ]

subprocess.run(cmd, capture_output=False, shell=False, text=True, check=True)
