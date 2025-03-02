import secrets

# INITIAL DATA
WORTHS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
SUITS = ('Clubs', 'Diamonds', 'Hearts', 'Spades')
TOTAL_CARDS_IN_DECK = len(WORTHS) * len(SUITS)
SINGLE_CARD_ODDS = 1 / TOTAL_CARDS_IN_DECK
SINGLE_WORTH_ODDS = len(SUITS) / TOTAL_CARDS_IN_DECK
SINGLE_SUIT_ODDS = len(WORTHS) / TOTAL_CARDS_IN_DECK


class Card(object):
    """ Class to represent an individual playing card. """
    def __init__(self, worth, suit):
        """
            Create an individual playing card.
        :param int worth: The value of the card.
        :param str suit: The suit of the card.
        """
        self.worth = worth
        self.suit = suit

    def __str__(self):
        """ Update string representation method of class to return the card's identity in a 'pretty' format. """
        if self.worth > 10:
            if self.worth == 11:
                _worth = "Jack"
            elif self.worth == 12:
                _worth = "Queen"
            elif self.worth == 13:
                _worth = "King"
            else:
                _worth = "Ace"
        else:
            _worth = self.worth
        return f"{_worth} of {self.suit}"


class Deck(object):
    """ Class to represent a full deck of playing cards. """
    def __init__(self):
        self.max_num_cards = 52
        self.available_cards = []
        for _s in SUITS:
            for _w in WORTHS:
                self.available_cards.append(Card(worth=_w, suit=_s))

    def deal_card(self):
        """
            Choose a card at random from the available cards in the deck and return it, removing it from the available
            cards in the deck.
        :return: The card chosen at random.
        :rtype: Card
        """
        card = secrets.choice(self.available_cards)
        self.available_cards.remove(card)
        return card

    @property
    def num_cards_available(self):
        """
            Get the number of available cards in the deck.  Can be useful for calculating odds.
        :return: integer representing the number of cards remaining in the deck.
        :rtype: int
        """
        return len(self.available_cards)


class Dealer(object):
    def __init__(self, num_players):
        self.deck = Deck()
        self.community_cards = []

    def deal_to_players(self, players):
        for i in range(2):
            for _player in players:
                _player.add_card(self.deck.deal_card())
        return

    def deal_flop(self, players):
        self._burn_card()

        for i in range(3):
            _card = self.deck.deal_card()
            self.community_cards.append(_card)

        for _player in players:
            _player.set_community_cards(self.community_cards)

    def deal_river(self, players):
        self._burn_card()

        _card = self.deck.deal_card()
        self.community_cards.append(_card)

        for _player in players:
            _player.set_community_cards(self.community_cards)

    def deal_turn(self, players):
        self._burn_card()

        _card = self.deck.deal_card()
        self.community_cards.append(_card)

        for _player in players:
            _player.set_community_cards(self.community_cards)

    def _burn_card(self):
        """
            Dealer removes a card from play.  This is known as 'burning' a card.
        :return:
        """
        _ = self.deck.deal_card()


if __name__ == '__main__':
    print("welcome to poker")
