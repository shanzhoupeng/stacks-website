import sqlite3
import config
from functions import *

# read all .aux files and generate a dictionary containing all labels and
# their whereabouts
def get_labels_from_source(path):
  # we'll do book.aux first, getting a complete overview of all labels
  aux_files = list_aux_files(path)
  aux_files.remove('book.aux') # do not parse this file again

  print 'Parsing book.aux'
  labels = parse_aux(path + 'book.aux') # generate dictionary with all labels
  
  print 'Parsing the other auxiliary files'
  # now merge every other .aux file against the current dictionary
  for aux_file in aux_files:
    print '  parsing {0}'.format(aux_file)
  
    local = parse_aux(path + aux_file)
    for label, information in local.iteritems():
      # we prepend the current filename to get the full label
      full_label = aux_file[0:-4] + '-' + label
  
      if full_label in labels:
        labels[full_label] = [aux_file[0:-4], labels[full_label], local[label]]
      else:
        print 'ERROR: the label \'{0}\' was found in {1} but not in {2}'.format(
            full_label, path + aux_file, path + 'book.aux')

  return labels

# read all tags from the current tags/tags file
def parse_tags(filename):
  tags_file = open(filename, 'r')

  tags = {}

  for line in tags_file:
    if not line.startswith('#'):
      (tag, label) = line.strip().split(',')
      tags[tag] = label

  tags_file.close()

  return tags

# check whether a tag exists in the database
def tag_exists(tag):
  count = 0

  try:
    query = 'SELECT tag FROM tags where tag = "' + tag + '"'
    cursor = connection.execute(query)

    if cursor.fetchone() != None: count = 1

  except sqlite3.Error, e:
    print "An error occurred:", e.args[0]

  return count > 0

# insert (or update) a tag
# TODO document the values, or create a Tag class
def insert_tag(tag, value):
  try:
    if tag_exists(tag):
      query = 'UPDATE tags SET label = ?, file = ?, chapter_page = ?, book_page = ?, book_id = ? WHERE tag = ?'
      connection.execute(query, (value[0], value[1], value[2], value[3], value[4], tag))
    else:
      query = 'INSERT INTO tags (tag, label, file, chapter_page, book_page, book_id) VALUES (?, ?, ?, ?, ?, ?)'
      connection.execute(query, (tag, value[0], value[1], value[2], value[3], value[4]))

  except sqlite3.Error, e:
    print "An error occurred:", e.args[0]

# create the tags database from scratch using the current tags/tags file
def import_tags(filename, labels):
  print 'Parsing the tags file'
  tags = parse_tags(filename)

  print 'Inserting (or updating) the tags'
  for tag, label in tags.iteritems():
    info = labels[label]
  
    insert_tag(tag, (label, info[0], info[2][1], info[1][1], info[1][0]))


connection = sqlite3.connect(config.database)

import_tags(config.tags_file, get_labels_from_source(config.tmp_folder))

connection.commit()
connection.close()