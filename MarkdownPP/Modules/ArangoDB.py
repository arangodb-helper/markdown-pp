# Copyright (C) 2014 ArangoDB GmbH
# Licensed under the MIT license

import re
import httplib, urllib
import os

from MarkdownPP.Module import Module
from MarkdownPP.Transform import Transform

chapter_re = re.compile('^!(BOOK|CHAPTER|SECTION|SUBSECTION|SUBSUBSECTION)\s+(.*\S)\s*$')
rest_re = re.compile("^@(REST[A-Z]*|EXAMPLES)\s*$")
rest_arg1_re = re.compile("^@(REST[A-Z]*|EXAMPLE_ARANGOSH_RUN)\{(\S*)\}\s*$")
rest_arg2_re = re.compile("^@(REST[A-Z]*)\{([^},]*),([^},]*)\}\s*$")
end_example_run_re = re.compile("^@END_EXAMPLE_ARANGOSH_RUN\s*$")

codere = re.compile("^(    |\t)")
linkre = re.compile("(\[(.*?)\][\(\[].*?[\)\]])")
fencedcodere = re.compile("^```\w*$")

class ArangoDB(Module):
  """
  Module to generate an anchored chapter.
  """

  @staticmethod
  def clean_title(title):
    for link in re.findall(linkre,title):
      title = title.replace(link[0],link[1])
    return title.replace(" ", "_")


  line = None
  linenum = None
  transforms = None
  dropExampleRun = False
    
  def head_lines(self):
    match = chapter_re.search(self.line)

    if match:
      type = match.group(1)
      text = match.group(2)
      tag = ArangoDB.clean_title(text).lower()

      if type == "BOOK":
        indent = "#"
      elif type == "CHAPTER":
              indent = "#"
      elif type == "SECTION":
              indent = "##"
      elif type == "SUBSECTION":
              indent = "###"
      elif type == "SUBSUBSECTION":
              indent = "####"

      anchor = '<a name=\"%s\"></a>\n' % tag
      header = '%s %s\n' % (indent, text)

      self.transforms.append(Transform(self.linenum, "swap", header))
      self.transforms.append(Transform(self.linenum, "prepend", anchor))

    return match


  def rest_example(self):
    match = rest_arg2_re.search(self.line)
    
  def transform(self, data):
    self.transforms = []
    self.linenum = 0
    self.dropExampleRun = False

    in_fenced_code_block = False

    for self.line in data:
      if self.dropExampleRun:
        match = end_example_run_re.search(self.line)

        if match:
          self.dropExampleRun = False

        self.transforms.append(Transform(self.linenum, "drop"))

      else:

        # Handling fenced code blocks (for Github-flavored markdown)
        if fencedcodere.search(self.line):
          if in_fenced_code_block:
            in_fenced_code_block = False
          else:
            in_fenced_code_block = True

        # Are we in a code block?
        if not in_fenced_code_block and not codere.search(self.line):
          done = self.head_lines()

          if not done:
            done = self.rest_example()

      self.linenum += 1

    return self.transforms