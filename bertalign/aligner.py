import numpy as np

from bertalign import model
from bertalign.corelib import *
from bertalign.utils import *

class Bertalign:
    def __init__(self,
                 src: str,
                 tgt: str ,
                 max_align: int = 5,
                 top_k: int = 3,
                 win: int = 5,
                 skip: float = -0.1,
                 margin: bool = True,
                 len_penalty: bool = True,
                 verbose: bool = True,
               ):
        
        self.max_align = max_align
        self.top_k = top_k
        self.win = win
        self.skip = skip
        self.margin = margin
        self.len_penalty = len_penalty
        self.verbose = verbose
        
        src = clean_text(src)
        tgt = clean_text(tgt)
        
        src_sents = src.splitlines()
        tgt_sents = tgt.splitlines()
 
        src_num = len(src_sents)
        tgt_num = len(tgt_sents)
        
        if self.verbose:
            print(f"Source number of sentences: {src_num}")
            print(f"Target number of sentences: {tgt_num}")
            print(f"Embedding source and target text using {model.model_name} ...")

        src_vecs, src_lens = model.transform(src_sents, max_align - 1)
        tgt_vecs, tgt_lens = model.transform(tgt_sents, max_align - 1)

        char_ratio = np.sum(src_lens[0,]) / np.sum(tgt_lens[0,])

        self.src_sents = src_sents
        self.tgt_sents = tgt_sents
        self.src_num = src_num
        self.tgt_num = tgt_num
        self.src_lens = src_lens
        self.tgt_lens = tgt_lens
        self.char_ratio = char_ratio
        self.src_vecs = src_vecs
        self.tgt_vecs = tgt_vecs
        
    def align_sents(self):
        if self.verbose:
            print("Performing first-step alignment ...")
        D, I = find_top_k_sents(self.src_vecs[0,:], self.tgt_vecs[0,:], k=self.top_k)
        first_alignment_types = get_alignment_types(2) # 0-1, 1-0, 1-1
        first_w, first_path = find_first_search_path(self.src_num, self.tgt_num)
        first_pointers = first_pass_align(self.src_num, self.tgt_num, first_w, first_path, first_alignment_types, D, I)
        first_alignment = first_back_track(self.src_num, self.tgt_num, first_pointers, first_path, first_alignment_types)
        
        if self.verbose:
            print("Performing second-step alignment ...")
        second_alignment_types = get_alignment_types(self.max_align)
        second_w, second_path = find_second_search_path(first_alignment, self.win, self.src_num, self.tgt_num)
        second_pointers = second_pass_align(self.src_vecs, self.tgt_vecs, self.src_lens, self.tgt_lens,
                                            second_w, second_path, second_alignment_types,
                                            self.char_ratio, self.skip, margin=self.margin, len_penalty=self.len_penalty)
        second_alignment = second_back_track(self.src_num, self.tgt_num, second_pointers, second_path, second_alignment_types)
        
        if self.verbose:
            print(f"Finished! Successfully aligning {self.src_num} sentences to {self.tgt_num} sentences\n")
        self.result = second_alignment
    
    def print_sents(self):
        for bead in (self.result):
            src_line = self._get_line(bead[0], self.src_sents)
            tgt_line = self._get_line(bead[1], self.tgt_sents)
            print(src_line + "\n" + tgt_line + "\n")

    @staticmethod
    def _get_line(bead, lines):
        line = ''
        if len(bead) > 0:
            line = ' '.join(lines[bead[0]:bead[-1]+1])
        return line
