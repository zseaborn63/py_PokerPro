import random
import secrets

# INITIAL DATA
from copy import deepcopy
from itertools import combinations

WORTHS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
SUITS = ('Clubs', 'Diamonds', 'Hearts', 'Spades')
TOTAL_CARDS_IN_DECK = len(WORTHS) * len(SUITS)
SINGLE_CARD_ODDS = 1 / TOTAL_CARDS_IN_DECK
SINGLE_WORTH_ODDS = len(SUITS) / TOTAL_CARDS_IN_DECK
SINGLE_SUIT_ODDS = len(WORTHS) / TOTAL_CARDS_IN_DECK


class EndGame(Exception):
    pass


class WinningHand(object):
    def __init__(self):
        self.close = False
        self.found = False
        self.ranking = None
        self.high_value = None
        self.odds = 0

    def get_sorted_cards(self, cards):
        copy_cards = deepcopy(cards)
        return sorted(copy_cards, key=lambda x: x.worth, reverse=True)

    @property
    def high_card(self):
        return self.high_value[0] if self.high_value is not None else None

    @property
    def outs(self):
        raise NotImplementedError()

    def calculate_odds(self, num_unseen_cards, remaining_community_cards):
        if remaining_community_cards > 0:
             raw = 1 - ((num_unseen_cards - self.outs) / num_unseen_cards) ** remaining_community_cards
        else:
            raw = 1 - ((num_unseen_cards - self.outs) / num_unseen_cards)
        self.odds = raw * 100

    def check_cards(self, cards):
        raise NotImplementedError()


class HighCard(WinningHand):
    def __init__(self):
        super(HighCard, self).__init__()
        self.ranking = 0

    def check_cards(self, cards):
        self.high_value = self.check_for_high_card(cards)
        self.found = True
        return self.found

    def check_for_high_card(self, cards):
        sorted_cards = self.get_sorted_cards(cards)
        return [sorted_cards[0], ]


class Pair(WinningHand):
    def __init__(self):
        super(Pair, self).__init__()
        self.ranking = 1
        self.num_to_match = 2

    def check_cards(self, cards):
        matched_cards = self.check_for_worth_matches(cards)
        if matched_cards:
            self.found = True
            self.high_value = matched_cards

        return self.found

    def check_for_worth_matches(self, cards):
        matches_found = []
        card_values = [x.worth for x in cards]
        if len(set(card_values)) < len(cards):
            sorted_cards = self.get_sorted_cards(cards)
            for _c in sorted_cards:
                if card_values.count(_c.worth) == self.num_to_match:
                    matches_found.append(_c)

        return matches_found


class TwoPair(Pair):
    def __init__(self):
        super(TwoPair, self).__init__()
        self.ranking = 2

    def check_cards(self, cards):
        local_cards = deepcopy(cards)

        pair_1 = self.check_for_worth_matches(local_cards)
        if pair_1:
            self.close = True
            for _c in pair_1:
                local_cards.remove(_c)
            pair_2 = self.check_for_worth_matches(local_cards)
            if pair_2:
                self.found = True
                self.high_value = pair_1 + pair_2

        return self.found

    @property
    def outs(self):
        return 2


class ThreeOfAKind(Pair):
    def __init__(self):
        super(ThreeOfAKind, self).__init__()
        self.ranking = 3
        self.num_to_match = 3

    def check_cards(self, cards):
        found = super(ThreeOfAKind, self).check_cards(cards)
        if not found:
            self.num_to_match = 2
            pair = self.check_for_worth_matches(cards)
            if pair:
                self.close = True
                self.high_value = pair

            self.num_to_match = 3

        return self.found

    @property
    def outs(self):
        return 3 - len(self.high_value)


class Straight(WinningHand):
    def __init__(self):
        super(Straight, self).__init__()
        self.ranking = 4
        self.num_matched = 0

    def check_cards(self, cards):
        straight_found = self.check_for_straight(cards)
        if straight_found:
            sorted_cards = self.get_sorted_cards(cards)
            self.high_value = sorted_cards
        else:
            # new function to see how close we are to a straight
            pass

        return straight_found

    def check_for_straight(self, cards):
        # todo: check for the many possible straight conditions that can be fullfilled if one is not found
        sorted_cards = self.get_sorted_cards(cards)
        _prev_val = None
        _interval = 1
        straight_found = True
        for _c in sorted_cards:
            if _prev_val is None:
                _prev_val = _c.worth
                continue

            if _c.worth != -_prev_val - _interval:
                straight_found = False
                break

        return straight_found


class Flush(WinningHand):
    def __init__(self):
        super(Flush, self).__init__()
        self.ranking = 5
        self.num_matched = 0

    def check_cards(self, cards):
        self.found = self.check_for_flush(cards)

        if self.found:
            self.high_value = self.get_sorted_cards(cards)

        return self.found

    def check_for_flush(self, cards):
        flush_found = False
        card_suits = [x.suit for x in cards]
        if len(set(card_suits)) == 1:
            flush_found = True
        else:
            suit_map = {}
            for _c in cards:
                if _c.suit not in suit_map.keys():
                    suit_map[_c.suit] = []
                suit_map[_c.suit].append(_c)
            four_card_suits = [suit for suit, cards in suit_map.items() if len(cards) == 4]
            if four_card_suits:
                self.close = True
                self.num_matched = 4
                self.high_value = suit_map[four_card_suits[0]]
            three_card_suits = [suit for suit, matches in suit_map.items() if len(matches) == 3]
            if three_card_suits:
                self.close = True
                self.num_matched = 3
                self.high_value = suit_map[three_card_suits[0]]

        return flush_found

    @property
    def outs(self):
        return 5 - len(self.high_value)


class FullHouse(WinningHand):
    def __init__(self):
        super(FullHouse, self).__init__()
        self.ranking = 6

    def check_cards(self, cards):
        pass


class FourOfAKind(Pair):
    def __init__(self):
        super(FourOfAKind, self).__init__()
        self.ranking = 7
        self.num_to_match = 4


class StraightFlush(Flush, Straight):
    def __init__(self):
        super(StraightFlush, self).__init__()
        self.ranking = 8
        self.is_royal = False

    def check_cards(self, cards):
        straight_flush_found = False
        straight_cards = []
        flush_cards = []

        flush_found = self.check_for_flush(cards)
        if self.close:
            flush_cards = deepcopy(self.high_value)

        straight_found = self.check_for_straight(cards)
        if self.close:
            straight_cards = deepcopy(self.high_value)

        if straight_found and flush_found:
            straight_flush_found = True
            self.high_value = self.get_sorted_cards(cards)
            if self.high_value[0].worth == 14:
                self.is_royal = True
        else:
            if straight_cards and flush_cards:
                self.close = True
                self.high_value = [x for x in straight_cards if x in flush_cards]

        return straight_flush_found

    @property
    def outs(self):
        return 5 - len()


WINNING_HANDS = (StraightFlush, FourOfAKind, FullHouse, Flush, Straight, ThreeOfAKind, TwoPair, Pair, HighCard)


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
        self.dealt_cards = []
        self.community_cards = []
        self.burnt_cards = []

        # Create the actual card instances
        for _s in SUITS:
            for _w in WORTHS:
                self.available_cards.append(Card(worth=_w, suit=_s))

        # Shuffle the cards a random number of times
        for _ in secrets.randbelow(7):
            random.shuffle(self.available_cards)

    def _deal_card(self):
        """
            Choose a card at random from the available cards in the deck and return it, removing it from the available
            cards in the deck.
        :return: The card chosen at random.
        :rtype: Card
        """
        card = secrets.choice(self.available_cards)
        self.available_cards.remove(card)
        return card

    def _find_card(self, worth, suit):
        """"""
        _card = None
        for _c in self.available_cards:
            if _c.suit == suit and _c.worth == worth:
                _card = _c
                break

        self.available_cards.remove(_card)
        return _card

    @property
    def num_cards_available(self):
        """
            Get the number of available cards in the deck.  Can be useful for calculating odds.
        :return: integer representing the number of cards remaining in the deck.
        :rtype: int
        """
        return len(self.available_cards)

    def get_player_card(self, card_str):
        """"""
        suit = card_str[-1]
        worth = card_str[:-1]
        return self._find_card(worth=worth, suit=suit)

    def set_community_card(self, card_str):
        """"""
        suit = card_str[-1]
        worth = card_str[:-1]
        return self._find_card(worth=worth, suit=suit)

    def deal_to_players(self, players, num_cards=2):
        for i in range(num_cards):
            for _player in players:
                _card = self._deal_card()
                _player.add_card(_card)
                self.dealt_cards.append(_card)
        return

    def deal_flop(self):
        self._burn_card()

        for i in range(3):
            _card = self._deal_card()
            self.community_cards.append(_card)

    def deal_river(self):
        self._burn_card()

        _card = self._deal_card()
        self.community_cards.append(_card)

    def deal_turn(self):
        self._burn_card()

        _card = self._deal_card()
        self.community_cards.append(_card)

    def _burn_card(self):
        """
            Dealer removes a card from play.  This is known as 'burning' a card.
        :return:
        """
        self.burnt_cards.append(self._deal_card())


class Player(object):

    def __init__(self, player_num):
        self.player_id = player_num
        self.cards = []
        self.best_hand = None
        self.odds = {}

        self._completed_hands = []
        self._possible_hands = []

    def add_card(self, card):
        self.cards.append(card)

    def get_card_combos(self, community_cards, num_cards=5):
        available_community_spots = num_cards - len(self.cards)
        _community = deepcopy(community_cards)
        combos_raw = combinations(_community, available_community_spots)
        combos = [list(x) for x in combos_raw]
        return combos

    def check_cards_for_winning_hands(self, community_cards):
        # Stats vars
        unseen = TOTAL_CARDS_IN_DECK - len(community_cards)
        remaining_community = 5 - len(community_cards)

        player_cards = deepcopy(self.cards)
        community_combos = self.get_card_combos(community_cards)

        for _combo in community_combos:
            player_hand = _combo + player_cards
            winning_hands = [x() for x in WINNING_HANDS]

            for _hand in winning_hands:
                completed = _hand.check_cards(player_hand)
                if completed:
                    self._completed_hands.append(_hand)
                    if self.best_hand is None:
                        self.best_hand = _hand
                    else:
                        if self.best_hand.ranking < _hand.ranking:
                            self.best_hand = _hand
                        elif self.best_hand.ranking == _hand.ranking:
                            current_highest = self.best_hand.high_value[0]
                            new_highest = _hand.high_value[0]
                            if new_highest > current_highest:
                                self.best_hand = _hand
                else:
                    if _hand.close:
                        self._possible_hands.append(_hand)
                        _hand.calculate_odds(num_unseen_cards=unseen,
                                             remaining_community_cards=remaining_community)

        return


class TexasHoldEm(object):
    def __init__(self, num_cards_per_player=2, num_players=6):

        self.num_cards_per_player = num_cards_per_player
        self.deck = Deck()

        # Need to define starting player:
        self.players = self._make_players(num_players=num_players)
        self.user_player = self.players[0].player_id
        self.dealer = self.players[0].player_id  # FIXME:  RANDOMIZE!

    def _make_players(self, num_players):
        return [Player(player_num=x) for x in range(num_players)]

    def _get_user_player(self):
        _user = None
        for _p in self.players:
            if _p.player_id == self.user_player:
                _user = _p
                break
        return _user

    @property
    def community_cards(self):
        return self.deck.community_cards

    def get_odds(self, player_cards, community_cards):
        user_player = self._get_user_player()
        for _cs in player_cards:
            user_player.add_card(self.deck.get_player_card(_cs))

        for _ccs in community_cards:
            self.deck.set_community_card(_ccs)

        user_player.check_cards_for_winning_hands(self.community_cards)

        # TODO: rest of the odds stuff
        return

    def get_win_percentage(self, num_games=1):
        num_user_wins = 0
        for _ in range(num_games):
            winning_player = self._play_hand()
            if winning_player == self.user_player:
                num_user_wins += 1
            self._end_hand()
        return

    def _play_hand(self):
        self.deck.deal_to_players(self.players)
        self.deck.deal_flop()
        leader = self._check_player_hands()
        self.deck.deal_river()
        leader = self._check_player_hands()
        self.deck.deal_turn()
        leader = self._check_player_hands()

        return leader.player_id

    def _end_hand(self):
        # Clear players hands
        self.players = self._make_players(len(self.players))

        # Get next dealer
        if self.dealer + 1 > len(self.players):
            self.dealer = self.players[0].player_id
        else:
            self.dealer += 1

        # Fresh deck and will be shuffled and have all cards in it
        self.deck = Deck()
        return

    def _check_player_hands(self):
        current_leader = None
        for _player in self.players:
            _player.check_cards_for_winning_hands(self.community_cards)
            if _player.best_hand is not None:
                if current_leader is None:
                    current_leader = _player
                else:
                    if _player.best_hand.ranking > current_leader.best_hand.ranking:
                        current_leader = _player
                    elif _player.best_hand.ranking == current_leader.best_hand.ranking:
                        current_highest = current_leader.best_hand.high_value[0]
                        new_highest = _player.best_hand.high_value[0]
                        if new_highest > current_highest:
                            current_leader = _player
        return current_leader


def test_player_wins():
    pass

def test_odds():
    pass


if __name__ == '__main__':
    print("welcome to poker")
    # TODO: MODES:
    #  1): "How Often Do I Win with this hand?"
    #  2): "What are my odds with this hand and these community cards?"
    try:
        while True:
            # TODO:
            #  1) get input from user for num players/cards
            #  2) New class to calculate odds; calculate and show player their odds
            #  3) Confirm player wants to continue
            pass
    except EndGame:
        print("Goodbye")
    except KeyboardInterrupt:
        print("Hard Exit")
    except Exception as e:
        print(f"Got a bad thing: {e}")
