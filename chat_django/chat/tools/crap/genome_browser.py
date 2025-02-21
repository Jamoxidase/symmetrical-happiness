import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from collections import defaultdict
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@dataclass
class GenomicRegion:
    genome: str
    chrom: str 
    start: int
    end: int
    tracks: Optional[List[str]] = None
    capture_screenshot: bool = True
    
    def __str__(self):
        return f"{self.genome} {self.chrom}:{self.start}-{self.end}"

@dataclass
class Feature:
    id: str  # Add this
    start: int
    end: int
    name: str
    type: str
    track: str
    score: Optional[float] = None
    raw_data: Dict = None  # Add this to store complete feature data
    
    def __str__(self):
        return f"{self.id}-{self.start}-{self.end}:{self.name}({self.track})"

@dataclass 
class GenomicResponse:
    """Container for genome browser query results"""
    region: GenomicRegion
    sequence: str
    features: List[Feature]
    annotated_sequence: str
    tracks: List[str]
    screenshot_path: Optional[str] = None  # Path to saved screenshot

    def generate_browser_link(self) -> str:
        """Generate UCSC Genome Browser link for the region"""
        base_url = "https://genome.ucsc.edu/cgi-bin/hgTracks?"
        position = f"{self.region.chrom}:{self.region.start}-{self.region.end}"
        params = [
            f"db={self.region.genome}",
            f"position={position}",
            "lastVirtModeType=default",
            "lastVirtModeExtraState=",
            "virtModeType=default",
            "virtMode=0",
            "nonVirtPosition="
        ]
        
        # Add track configurations
        for track in self.tracks:
            params.append(f"{track}=pack")
            
        return base_url + "&".join(params)
        
    def capture_browser_screenshot(self) -> tuple[str, bytes]:
        """Capture a screenshot of the UCSC Genome Browser view
        
        Returns:
            Tuple of (filename, image_bytes)
            
        Raises:
            RuntimeError: If screenshot capture fails
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.region.genome}_{self.region.chrom}_{self.region.start}_{self.region.end}_{timestamp}.png"
                
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=chrome_options)
            try:
                url = self.generate_browser_link()
                driver.get(url)
                driver.implicitly_wait(10)
                image_bytes = driver.get_screenshot_as_png()
                return filename, image_bytes
            finally:
                driver.quit()
        except Exception as e:
            raise RuntimeError(f"Failed to capture screenshot: {str(e)}")

    def __str__(self):
        return f"""
                Region: {self.region}
                Sequence length: {len(self.sequence)}
                Features: {len(self.features)}
                Browser link: {self.generate_browser_link()}"""


class AnnotatedSequence:
    def __init__(self, sequence: str, region_start: int):
        self.sequence = sequence
        self.region_start = region_start
        self.features = []
        
    def add_feature(self, feature: Feature):
        """Add a feature to the sequence"""
        rel_start = feature.start - self.region_start
        rel_end = feature.end - self.region_start
        
        rel_start = max(0, rel_start)
        rel_end = min(len(self.sequence), rel_end)
        
        if rel_start < len(self.sequence) and rel_end > rel_start:
            self.features.append((rel_start, rel_end, feature))

    def format_sequence(self) -> str:
        sorted_features = sorted(
            self.features,
            key=lambda x: (x[0], -1 * (x[1] - x[0]))
        )
        
        annotations = []
        for start, end, feature in sorted_features:
            annotations.append((start, f'[{feature.id}-{feature.track}:{feature.start}-{feature.end}:{feature.name}|'))
            annotations.append((end, f'|{feature.id}-{feature.track}:{feature.start}-{feature.end}:{feature.name}]'))
            
        annotations.sort(key=lambda x: (x[0], x[1].startswith('|')))
        
        result = ''
        pos = 0
        for ann_pos, ann_text in annotations:
            while pos < ann_pos and pos < len(self.sequence):
                result += self.sequence[pos]
                pos += 1
            result += ann_text
            
        while pos < len(self.sequence):
            result += self.sequence[pos]
            pos += 1
            
        return result


class GenomeBrowser:
    DEFAULT_TRACKS = [
        "knownGene",
        "encodeCcreCombined",
        "encode3RenEnhancerEpdNewPromoter",
        "refSeqComposite",
        "wgEncodeBroadHmm",
        "cpgIslandExt",
        "cons100way",
        "tRNAs",
        "Enhancers",
        "wgEncodeAwgDnaseUniform",
        "wgEncodeRegDnaseClustered",
        "wgEncodeRegTfbsClusteredV3",
        "wgEncodeMapability",
        "rmsk"
    ]
    
    def __init__(self, debug=True):
        self.base_url = "https://api.genome.ucsc.edu"
        self.debug = debug
        
    def _debug_print(self, msg: str, data: any = None):
        if self.debug:
            print(f"[DEBUG] {msg}")
            if data:
                if isinstance(data, (dict, list)):
                    print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
                else:
                    print(str(data))

    def get_sequence(self, region: GenomicRegion) -> Dict:
        """Get DNA sequence for region"""
        self._debug_print(f"Fetching sequence for {region}")
        url = f"{self.base_url}/getData/sequence"
        params = {
            "genome": region.genome,
            "chrom": region.chrom,
            "start": region.start,
            "end": region.end
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_track_data(self, region: GenomicRegion, track: str) -> Dict:
        """Get data for a specific track in region"""
        self._debug_print(f"Fetching track {track} for {region}")
        url = f"{self.base_url}/getData/track"
        params = {
            "genome": region.genome,
            "track": track,
            "chrom": region.chrom,
            "start": region.start,
            "end": region.end
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except:
            self._debug_print(f"Error fetching track {track}")
            return {}

    def extract_features(self, track_data: Dict, track: str) -> List[Feature]:
        features = []
        feature_id = 0
        
        items = []
        if isinstance(track_data, dict):
            if track in track_data:
                items = track_data[track]
            else:
                items = [track_data]
        elif isinstance(track_data, list):
            items = track_data
            
        self._debug_print(f"Processing {len(items)} items for track {track}")
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            start = None
            end = None
            name = None
            
            for field in ['chromStart', 'txStart', 'start', 'begin']:
                if field in item:
                    start = int(item[field])
                    break
                    
            for field in ['chromEnd', 'txEnd', 'end', 'stop']:
                if field in item:
                    end = int(item[field])
                    break
                    
            for field in ['name', 'id', 'gene', 'transcript']:
                if field in item and item[field]:
                    name = str(item[field])
                    break
                    
            if start is not None and end is not None:
                feature_id += 1
                features.append(Feature(
                    id=f"id{feature_id:05d}",
                    start=start,
                    end=end,
                    name=name or 'unnamed',
                    type=track,
                    track=track,
                    score=item.get('score'),
                    raw_data=item
                ))
        
        return features

    def get_available_tracks(self, region: GenomicRegion) -> List[str]:
        """Get list of available tracks for a region"""
        url = f"{self.base_url}/list/tracks"
        params = {
            "genome": region.genome,
        }
        response = requests.get(url, params=params)
        tracks_data = response.json()[region.genome]
        return list(tracks_data.keys())

    def view_region(self, region: GenomicRegion) -> GenomicResponse:
        """View a genomic region with specified tracks
        
        Args:
            region: GenomicRegion object specifying location and optional tracks
                   If tracks not provided, uses DEFAULT_TRACKS
        
        Returns:
            GenomicResponse object containing:
            - region: GenomicRegion object
            - sequence: DNA sequence string
            - features: List of Feature objects found in region
            - annotated_sequence: Sequence with feature annotations
            - tracks: List of tracks that were displayed
            
            The object also has methods:
            - generate_browser_link(): Get UCSC browser URL
            - capture_browser_screenshot(): Take screenshot and return path
            
        Example:
            # Use default tracks
            region = GenomicRegion(genome="hg19", chrom="chr19", start=1000, end=2000)
            response = browser.view_region(region)
            
            # Specify tracks
            region = GenomicRegion(
                genome="hg19", 
                chrom="chr19", 
                start=1000, 
                end=2000,
                tracks=["knownGene", "tRNAs"]
            )
            response = browser.view_region(region)
        """
        tracks_to_show = region.tracks if region.tracks is not None else self.DEFAULT_TRACKS
        
        # Get sequence
        sequence_data = self.get_sequence(region)
        if not sequence_data or 'dna' not in sequence_data:
            raise ValueError("Could not retrieve sequence")
            
        sequence = sequence_data['dna']
        all_features = []
        annotated_seq = AnnotatedSequence(sequence, region.start)
        
        # Get features from each track
        for track in tracks_to_show:
            track_data = self.get_track_data(region, track)
            features = self.extract_features(track_data, track)
            all_features.extend(features)
            for feature in features:
                annotated_seq.add_feature(feature)
                
        response = GenomicResponse(
            region=region,
            sequence=sequence,
            features=sorted(all_features, key=lambda f: (f.start, f.end)),
            annotated_sequence=annotated_seq.format_sequence(),
            tracks=tracks_to_show
        )
        
        # Take screenshot if requested
        if region.capture_screenshot:
            response.screenshot_path = response.capture_browser_screenshot()
            self._debug_print(f"Screenshot saved to: {response.screenshot_path}")
            
        return response


def main():
    browser = GenomeBrowser(debug=True)
    region = GenomicRegion(
        genome="hg19",
        chrom="chr19", 
        start=45980518,
        end=45983027,
    )

    # Get available tracks
    available_tracks = browser.get_available_tracks(region)
    print(f"Available tracks: {available_tracks}")

    # View with specific tracks including tRNAs
    tracks_to_view = [
        "knownGene",
        "encodeCcreCombined",
        "encode3RenEnhancerEpdNewPromoter",
        "refSeqComposite",
        "wgEncodeBroadHmm",
        "cpgIslandExt",
        "cons100way",
        "tRNAs",
        "Enhancers",
        "wgEncodeAwgDnaseUniform",
        "wgEncodeRegDnaseClustered",
        "wgEncodeRegTfbsClusteredV3",
        "wgEncodeMapability",
        "rmsk"
    ]
    
    response = browser.view_region(region, tracks=tracks_to_view)
    
    print(response)  # This will now include the browser link
    print("\nDetailed Features:")
    for f in response.features:
        print(f"\nFeature {f.id}:")
        print(f"  Position: {f.start}-{f.end}")
        print(f"  Name: {f.name}")
        print(f"  Track: {f.track}")
        if f.score is not None:
            print(f"  Score: {f.score}")
        if f.raw_data:
            print("  Raw data:")
            print(json.dumps(f.raw_data, indent=4))
    
    print("\nAnnotated Sequence:")
    print(response.annotated_sequence)
    print("\nSequence:")
    print(response.sequence)
    print("\nBrowser Link:")
    print(response.generate_browser_link())
    
    print("\nCapturing screenshot...")
    screenshot_path = response.capture_browser_screenshot()
    print(f"Screenshot saved to: {screenshot_path}")

if __name__ == "__main__":
    main()