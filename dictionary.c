/**
 * Implements a dictionary's functionality.
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>

#include "dictionary.h"

#define HASHTABLE_SIZE 27

node *hashtable[HASHTABLE_SIZE] = {NULL};
unsigned int word_count = 0;
bool loaded = false;
char *dict_word = NULL;
char *lower = NULL;
char *lower_word = NULL;

/* hash function found at https://www.reddit.com/r/cs50/comments/1x6vc8/pset6_trie_vs_hashtable/ */
int hash_it(char* needs_hashing)
{
    unsigned int hash = 0;
    for (int i=0, n=strlen(needs_hashing); i<n; i++)
        hash = (hash << 2) ^ needs_hashing[i];
    return hash % HASHTABLE_SIZE;
}

/**
 * Returns true if word is in dictionary else false.
 */
bool check(const char *word)
{
    int word_length = strlen(word);
    
    lower = malloc(word_length + 1);
    lower_word = lower;

    for (int j = 0; j < word_length; j++)
    {
        lower_word[j] = tolower(word[j]);
    }
    
    lower_word[word_length] = '\0';
    
    node *pointer = hashtable[hash_it(lower_word)];

    while (pointer != NULL)
    {
        if (strcasecmp(pointer->word, lower_word) == 0)
            {
                free(lower);
                return true;
            }

        else pointer = pointer->next; 
    }
    free(lower);
    return false;
}

/**
 * Loads dictionary into memory. Returns true if successful else false.
 */
bool load(const char *dictionary)
{
    FILE *inptr = fopen(dictionary, "r");
    
    if (inptr == NULL)
    {
        fprintf(stderr, "Dictionary cannot be read\n");
        return 1;
    }
    
    dict_word = malloc((sizeof(char)*LENGTH) + 1);
    
    while(fscanf(inptr, "%s", dict_word) != EOF)
    {
        node *new_node = malloc(sizeof(node));
        if (new_node == NULL)
        {
            unload();
            free(new_node);
            return false;
        }
        else
        {
            strcpy(new_node->word, dict_word);
            if (dict_word != NULL)
            {
                new_node->next = hashtable[hash_it(dict_word)];
                hashtable[hash_it(dict_word)] = new_node;
                word_count++;
            }
            else return false;
        }
    }
    fclose(inptr);
    loaded = true;
    return true;
}

/**
 * Returns number of words in dictionary if loaded else 0 if not yet loaded.
 */
unsigned int size(void)
{
    if (loaded == true)
    return word_count;
    else return 0;
}

/**
 * Unloads dictionary from memory. Returns true if successful else false.
 */
bool unload(void)
{
    for (int i = 0; i < HASHTABLE_SIZE; i++)
    {
        node *head = hashtable[i];
        while (head != NULL)
        {
            node *temp = head;
            head = head->next;
            free(temp);
        }
        if (head != NULL) 
        {
            return false;
        }
    }
    free(dict_word);
    return true;
}
