
class WordRestrictionValidator:

  def __init__(self, restricted_words):
    self.restricted_words = restricted_words

  def validate(self, text):
    words = text.split()
    for word in words:
      if word.casefold() in self.restricted_words:
        return True
      return False
    